"""
CLI commands for security testing.
"""

from pathlib import Path

import click

from ...security import (
    ComplianceStandard,
    ComplianceValidator,
    OWASPScanner,
    PenetrationTester,
    SecretDetector,
    SecurityReporter,
)


@click.group(name="security-test")
def security_cli():
    """Security testing commands."""
    pass


@security_cli.command()
@click.option("--target", "-t", required=True, help="Target URL to scan")
@click.option("--method", "-m", default="GET", help="HTTP method")
@click.option("--output", "-o", help="Output file for report")
def owasp(target, method, output):
    """Run OWASP Top 10 vulnerability scan."""
    click.echo(f"🔍 Running OWASP Top 10 scan on {target}...")

    scanner = OWASPScanner()
    result = scanner.scan_endpoint(target, method=method)

    click.echo("\n📊 Scan Results:")
    click.echo(f"   Status: {result.status}")
    click.echo(f"   Total Findings: {result.total_findings}")
    click.echo(f"   Critical: {result.critical_count}")
    click.echo(f"   High: {result.high_count}")
    click.echo(f"   Medium: {result.medium_count}")
    click.echo(f"   Low: {result.low_count}")

    if result.vulnerabilities:
        click.echo("\n🚨 Vulnerabilities Found:")
        for vuln in result.vulnerabilities[:10]:
            click.echo(f"   [{vuln.severity.value.upper()}] {vuln.title}")
            click.echo(f"      Category: {vuln.category.value}")
            click.echo(f"      Remediation: {vuln.remediation[:100]}...")

    if output:
        reporter = SecurityReporter()
        reporter.add_scan_result(result)
        reporter.export_json(output)
        click.echo(f"\n📄 Report saved to {output}")


@security_cli.command()
@click.option("--target", "-t", required=True, help="Target URL")
@click.option("--output", "-o", help="Output file for report")
def pentest(target, output):
    """Run penetration testing."""
    click.echo(f"🎯 Running penetration tests on {target}...")

    tester = PenetrationTester()

    # Test authentication bypass
    result = tester.test_authentication_bypass(target, target)

    click.echo("\n📊 Penetration Test Results:")
    click.echo(f"   Total Findings: {result.total_findings}")

    if output:
        reporter = SecurityReporter()
        reporter.add_scan_result(result)
        reporter.export_json(output)


@security_cli.command()
@click.option("--target", "-t", required=True, help="Target URL")
@click.option(
    "--standard",
    "-s",
    multiple=True,
    type=click.Choice(["gdpr", "pci_dss", "hipaa", "soc2", "iso27001"]),
    help="Compliance standard to validate",
)
@click.option("--output", "-o", help="Output file for report")
def compliance(target, standard, output):
    """Run compliance validation."""
    click.echo(f"📋 Running compliance validation on {target}...")

    validator = ComplianceValidator()

    standards = (
        [ComplianceStandard(s) for s in standard]
        if standard
        else [ComplianceStandard.GDPR]
    )

    all_violations = []
    for std in standards:
        click.echo(f"   Checking {std.value}...")
        if std == ComplianceStandard.GDPR:
            violations = validator.validate_gdpr(target, collects_pii=True)
        elif std == ComplianceStandard.PCI_DSS:
            violations = validator.validate_pci_dss(target, processes_payments=True)
        elif std == ComplianceStandard.HIPAA:
            violations = validator.validate_hipaa(target, handles_phi=True)
        all_violations.extend(violations)

    click.echo("\n📊 Compliance Results:")
    click.echo(f"   Total Violations: {len(all_violations)}")

    if all_violations:
        click.echo("\n⚠️  Violations Found:")
        for violation in all_violations[:10]:
            click.echo(f"   [{violation.severity.value.upper()}] {violation.title}")
            click.echo(f"      Standard: {violation.standard.value}")
            click.echo(f"      Requirement: {violation.requirement}")

    if output:
        reporter = SecurityReporter()
        reporter.add_compliance_violations(all_violations)
        reporter.export_json(output)
        click.echo(f"\n📄 Report saved to {output}")


@security_cli.command()
@click.option("--path", "-p", required=True, help="File or directory to scan")
@click.option("--output", "-o", help="Output file for report")
@click.option("--include-pii/--no-pii", default=True, help="Include PII detection")
def secrets(path, output, include_pii):
    """Scan for exposed secrets and PII."""
    click.echo(f"🔐 Scanning for secrets in {path}...")

    detector = SecretDetector()

    path_obj = Path(path)
    if path_obj.is_file():
        findings = detector.scan_file(str(path_obj), include_pii=include_pii)
    else:
        findings = detector.scan_directory(str(path_obj), include_pii=include_pii)

    click.echo("\n📊 Secret Scan Results:")
    click.echo(f"   Total Findings: {len(findings)}")

    if findings:
        click.echo("\n🚨 Secrets Found:")
        for finding in findings[:20]:
            click.echo(f"   [{finding.severity.value.upper()}] {finding.type.value}")
            click.echo(f"      Location: {finding.file_path or finding.endpoint}")
            click.echo(f"      Content: {finding.masked_content}")

    if output:
        reporter = SecurityReporter()
        reporter.add_secrets(findings)
        reporter.export_json(output)
        click.echo(f"\n📄 Report saved to {output}")


@security_cli.command()
@click.option("--target", "-t", required=True, help="Target URL")
@click.option("--output", "-o", default="security-report.json", help="Output file")
def full_scan(target, output):
    """Run comprehensive security scan."""
    click.echo(f"🔒 Running comprehensive security scan on {target}...")

    reporter = SecurityReporter(project_name=target)

    # OWASP Scan
    click.echo("\n1️⃣ Running OWASP Top 10 scan...")
    owasp_scanner = OWASPScanner()
    owasp_result = owasp_scanner.scan_endpoint(target)
    reporter.add_scan_result(owasp_result)
    click.echo(f"   Found {owasp_result.total_findings} vulnerabilities")

    # Secret Detection
    click.echo("\n2️⃣ Scanning for secrets...")
    # Note: This would scan API responses in real implementation

    # Compliance Check
    click.echo("\n3️⃣ Checking compliance...")
    validator = ComplianceValidator()
    gdpr_violations = validator.validate_gdpr(target, collects_pii=True)
    reporter.add_compliance_violations(gdpr_violations)
    click.echo(f"   Found {len(gdpr_violations)} compliance violations")

    # Generate Report
    click.echo("\n📊 Generating Report...")
    report = reporter.generate_report()

    click.echo("\n🎯 Summary:")
    click.echo(
        f"   Risk Score: {report.risk_score:.1f}/100 ({report.risk_level.upper()})"
    )
    click.echo(f"   Vulnerabilities: {report.total_vulnerabilities}")
    click.echo(f"   Secrets: {report.total_secrets}")
    click.echo(f"   Compliance Violations: {report.total_compliance_violations}")

    if report.top_recommendations:
        click.echo("\n💡 Top Recommendations:")
        for i, rec in enumerate(report.top_recommendations, 1):
            click.echo(f"   {i}. {rec}")

    # Export
    reporter.export_json(output)
    click.echo(f"\n📄 Full report saved to {output}")


def register_security_commands(cli):
    """Register security commands with CLI."""
    cli.add_command(security_cli)
