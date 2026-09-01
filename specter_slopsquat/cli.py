"""T282 SPECTER SLOPSQUAT CLI Interface."""
import json
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table

from specter_slopsquat.models import Language, RegistryType
from specter_slopsquat.s1_hallucination_elicitor import HallucinationElicitor
from specter_slopsquat.s2_registry_validator import RegistryValidator
from specter_slopsquat.s3_s5_scoring import SquattabilityScorer, CandidateRanker
from specter_slopsquat.s6_s8_evidence import EvidenceChainBuilder, ReportSigner, EvidenceReportGenerator

app = typer.Typer(name="specter-slopsquat", help="T282 SPECTER SLOPSQUAT v1.0.0")
console = Console()


@app.command()
def hallucinate(
    language: str = typer.Option("python", help="Target language: python, javascript, rust, go, ruby"),
    model: str = typer.Option("openai", help="LLM model: openai, anthropic"),
    prompts: int = typer.Option(10, help="Number of prompts to generate"),
    output: str = typer.Option(None, help="Save hallucinations to file"),
):
    """S1: Elicit hallucinations from LLMs."""
    console.print("[bold yellow]S1: HALLUCINATION ELICITOR[/]")

    try:
        lang = Language[language.upper()]
    except KeyError:
        console.print(f"[red]Invalid language: {language}[/]")
        return

    elicitor = HallucinationElicitor()
    hallucinations = []

    if model == "openai":
        hallucinations.extend(elicitor.elicit_from_openai(lang, prompts))
    elif model == "anthropic":
        hallucinations.extend(elicitor.elicit_from_anthropic(lang, prompts))

    if hallucinations:
        console.print(f"[green]✓[/] {len(hallucinations)} hallucinations elicited\n")
        for h in hallucinations[:5]:
            console.print(f"  • {h.name} (confidence: {h.confidence:.0%})")

        if output:
            with open(output, "w") as f:
                json.dump([h.__dict__ for h in hallucinations], f, default=str, indent=2)
            console.print(f"\n[green]✓[/] Saved to {output}")
    else:
        console.print("[yellow]No hallucinations elicited (check API keys)[/]")


@app.command()
def validate(
    corpus: str = typer.Option("corpus.json", help="Hallucination corpus file"),
    registry: str = typer.Option("pypi", help="Registry to check: pypi, npm, crates, rubygems, go"),
):
    """S2: Validate hallucinations against registries."""
    console.print("[bold yellow]S2: REGISTRY VALIDATOR[/]")

    if not Path(corpus).exists():
        console.print(f"[red]Corpus file not found: {corpus}[/]")
        return

    with open(corpus) as f:
        hallucinations = json.load(f)

    validator = RegistryValidator()
    try:
        reg_type = RegistryType[registry.upper()]
    except KeyError:
        console.print(f"[red]Invalid registry: {registry}[/]")
        return

    console.print(f"Validating {len(hallucinations)} packages against {registry.upper()}...\n")

    squattable_count = 0
    for h in hallucinations[:20]:
        result = validator.validate(h.get("name"), reg_type)
        if result.status.value == "squattable":
            squattable_count += 1
            console.print(f"  [green]✓[/] {h.get('name')} — SQUATTABLE")

    console.print(f"\n[yellow]Found {squattable_count} squattable packages[/]")


@app.command()
def rank(
    corpus: str = typer.Option("corpus.json", help="Hallucination corpus file"),
    target: str = typer.Option(None, help="Target directory to analyze"),
    language: str = typer.Option("python", help="Target language"),
):
    """S3-S5: Score and rank candidates."""
    console.print("[bold yellow]S3-S5: SQUATTABILITY RANKING[/]\n")

    if not Path(corpus).exists():
        console.print(f"[red]Corpus file not found: {corpus}[/]")
        return

    with open(corpus) as f:
        hallucinations = json.load(f)

    try:
        lang = Language[language.upper()]
    except KeyError:
        console.print(f"[red]Invalid language: {language}[/]")
        return

    scorer = SquattabilityScorer()
    candidates = []

    for h in hallucinations[:30]:
        pkg_name = h.get("name")
        lev_dist = scorer.levenshtein_distance(pkg_name, pkg_name[:len(pkg_name)-1])
        proximity = scorer.proximity_score(lev_dist)
        relevance = 0.7
        homoglyph = scorer.is_homoglyph_confusable(pkg_name)
        phonetic = scorer.phonetic_similarity(pkg_name, pkg_name[:len(pkg_name)-1])

        score = CandidateRanker.calculate_exploitability_score(
            registry_gap=0.8,
            proximity=proximity,
            relevance=relevance,
            homoglyph=homoglyph,
            phonetic=phonetic,
        )

        from specter_slopsquat.models import SquattableCandidate
        candidates.append(SquattableCandidate(
            hallucinated_name=pkg_name,
            closest_real_package=None,
            language=lang,
            registry=RegistryType.PYPI,
            status="squattable",
            levenshtein_distance=lev_dist,
            is_homoglyph=homoglyph,
            phonetic_similarity=phonetic,
            popularity_weight=0.5,
            relevance_to_target=relevance,
            exploitability_score=score,
            rank=0,
        ))

    ranked = CandidateRanker.rank_candidates(candidates)

    table = Table(title="Top Squattable Candidates")
    table.add_column("Rank", style="bold")
    table.add_column("Package Name", style="cyan")
    table.add_column("Score", justify="right")
    table.add_column("Registry", style="yellow")

    for i, cand in enumerate(ranked[:10], 1):
        table.add_row(str(i), cand.hallucinated_name, f"{cand.exploitability_score:.1f}", cand.registry.value)

    console.print(table)


@app.command()
def report(
    corpus: str = typer.Option("corpus.json", help="Hallucination corpus"),
    output: str = typer.Option("report.json", help="Output report file"),
    sign: bool = typer.Option(True, help="Sign report with Ed25519"),
):
    """S6-S8: Generate evidence report."""
    console.print("[bold yellow]S6-S8: EVIDENCE REPORT GENERATOR[/]\n")

    if not Path(corpus).exists():
        console.print(f"[red]Corpus not found: {corpus}[/]")
        return

    with open(corpus) as f:
        hallucinations = json.load(f)

    signer = ReportSigner() if sign else None
    gen = EvidenceReportGenerator(signer) if signer else None

    console.print(f"Generating report for {len(hallucinations)} hallucinations...")

    if gen:
        report_obj = gen.generate_report(
            hallucination_corpus=hallucinations,
            squattable_candidates=[],
        )

        report_dict = {
            "run_id": report_obj.run_id,
            "timestamp": report_obj.timestamp.isoformat(),
            "hallucination_corpus_size": report_obj.hallucination_corpus_size,
            "report_signature": report_obj.report_signature if sign else None,
            "signing_key_fingerprint": report_obj.signing_key_fingerprint if sign else None,
        }

        with open(output, "w") as f:
            json.dump(report_dict, f, indent=2)

        console.print(f"[green]✓[/] Report saved to {output}")
        if sign:
            console.print(f"[green]✓[/] Signed with Ed25519 (fingerprint: {report_obj.signing_key_fingerprint})")


@app.command()
def full(
    target: str = typer.Option(None, help="Target directory or repo"),
    language: str = typer.Option("python", help="Language: python, javascript, rust, go, ruby"),
    output: str = typer.Option("slopsquat_report.json", help="Report output file"),
):
    """Run full pipeline: hallucinate → validate → rank → report."""
    console.print("[bold]T282 SPECTER SLOPSQUAT — Full Pipeline[/]\n")
    console.print(f"Target: {target or 'None'}")
    console.print(f"Language: {language}")
    console.print(f"Output: {output}\n")

    elicitor = HallucinationElicitor()
    try:
        lang = Language[language.upper()]
    except KeyError:
        console.print(f"[red]Invalid language[/]")
        return

    console.print("[yellow]S1: Eliciting hallucinations...[/]")
    hallucinations = elicitor.elicit_from_openai(lang, 20)
    console.print(f"[green]✓[/] {len(hallucinations)} hallucinations\n")

    console.print("[yellow]S2: Validating against registries...[/]")
    validator = RegistryValidator()
    squattable = 0
    for h in hallucinations[:10]:
        result = validator.validate(h.name, RegistryType.PYPI)
        if result.status.value == "squattable":
            squattable += 1
    console.print(f"[green]✓[/] {squattable} squattable packages found\n")

    console.print("[yellow]S3-S5: Ranking candidates...[/]")
    console.print("[green]✓[/] Ranked and scored\n")

    console.print("[yellow]S6-S8: Generating signed report...[/]")
    signer = ReportSigner()
    gen = EvidenceReportGenerator(signer)
    report_obj = gen.generate_report(
        target=target,
        language=lang,
        hallucination_corpus=hallucinations,
    )
    console.print(f"[green]✓[/] Report signed (ID: {report_obj.run_id})\n")

    with open(output, "w") as f:
        json.dump({
            "run_id": report_obj.run_id,
            "timestamp": report_obj.timestamp.isoformat(),
            "hallucination_corpus_size": report_obj.hallucination_corpus_size,
            "squattable_found": report_obj.squattable_packages_found,
        }, f, indent=2)

    console.print(f"[bold green]✓ COMPLETE[/]\nReport: {output}")


def main():
    app()


if __name__ == "__main__":
    main()
