"""
Certificate management commands.
"""
import shutil
from pathlib import Path
from .base import Command, register
from ..console import Output, Style
from ..utils import PathManager, PackageManager


CERTS_DIR = Path("certs")


def get_certificate_files(certs_dir: Path = CERTS_DIR) -> list:
    """Find all .pem and .crt certificate files in the certs directory."""
    if not certs_dir.exists():
        return []
    return sorted(
        p for p in certs_dir.iterdir()
        if p.is_file() and p.suffix in (".pem", ".crt")
    )


def _ensure_certifi() -> bool:
    """Ensure certifi is installed in the project's environment."""
    try:
        import certifi
        return True
    except ImportError:
        Output.info("Installing certifi...")
        if PackageManager.install(["certifi"]):
            return True
        Output.error("Failed to install certifi")
        return False


def append_certificates_to_certifi(certs_dir: Path = CERTS_DIR) -> bool:
    """
    Append all certificates from the certs/ directory to the certifi CA bundle.

    Returns True if at least one certificate was appended.
    """
    if not _ensure_certifi():
        return False

    import certifi

    cert_files = get_certificate_files(certs_dir)
    if not cert_files:
        Output.warn(f"No certificate files (.pem, .crt) found in {certs_dir}/")
        return False

    ca_bundle = certifi.where()
    backup_path = ca_bundle + ".backup"

    # Create a backup only if one doesn't already exist
    if not Path(backup_path).exists():
        shutil.copy(ca_bundle, backup_path)
        Output.info(f"Backup of CA bundle created at {backup_path}")

    appended = 0
    ca_bundle_content = Path(ca_bundle).read_bytes()

    for cert_path in cert_files:
        cert_data = cert_path.read_bytes().strip()

        # Skip if certificate is already in the bundle
        if cert_data in ca_bundle_content:
            Output.info(f"Certificate already in bundle: {cert_path.name}")
            continue

        with open(ca_bundle, "ab") as bundle:
            bundle.write(b"\n")
            bundle.write(cert_data)
            bundle.write(b"\n")

        Output.success(f"Appended: {cert_path.name}")
        appended += 1

    if appended:
        Output.success(f"{appended} certificate(s) appended to certifi CA bundle")
    else:
        Output.info("No new certificates to append (all already present)")

    return appended > 0


@register
class InstallCertificateCommand(Command):
    signature = "install:certificate"
    description = "Append custom SSL certificates to the certifi CA bundle"
    help = """
Examples:
  fastman install:certificate

Place your .pem or .crt certificate files in the certs/ directory
at the root of your project, then run this command.
"""

    def handle(self):
        Output.info("Certificate Manager")
        Output.new_line()

        certs_dir = CERTS_DIR

        # Check if certs directory exists
        if not certs_dir.exists():
            Output.warn(f"Directory '{certs_dir}/' not found.")
            Output.info("Creating certs/ directory...")
            PathManager.ensure_dir(certs_dir)
            # Remove the __init__.py that ensure_dir creates (not a Python package)
            init_file = certs_dir / "__init__.py"
            if init_file.exists():
                init_file.unlink()
            Output.new_line()
            Output.info("Next steps:")
            Output.echo(f"  1. Place your .pem or .crt files in the certs/ directory", Style.CYAN)
            Output.echo(f"  2. Run: fastman install:certificate", Style.CYAN)
            return

        # Find certificates
        cert_files = get_certificate_files(certs_dir)
        if not cert_files:
            Output.warn(f"No certificate files (.pem, .crt) found in {certs_dir}/")
            Output.info("Place your certificate files in the certs/ directory and try again.")
            return

        Output.info(f"Found {len(cert_files)} certificate(s):")
        for f in cert_files:
            Output.echo(f"  {f.name}", Style.GREEN)
        Output.new_line()

        # Append certificates
        append_certificates_to_certifi(certs_dir)

        Output.new_line()
        Output.info("The certificates are now trusted by Python's requests/httpx/aiohttp libraries.")
