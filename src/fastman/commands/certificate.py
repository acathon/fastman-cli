"""Certificate bundle management commands."""
from pathlib import Path

from .base import Command, register
from ..console import Output, Style
from ..utils import EnvManager, PathManager, PackageManager


CERTS_DIR = Path("certs")
MERGED_CA_BUNDLE_NAME = "ca-bundle-merged.pem"


def get_certificate_files(certs_dir: Path = CERTS_DIR) -> list:
    """Find all .pem and .crt certificate files in the certs directory."""
    if not certs_dir.exists():
        return []
    return sorted(
        p for p in certs_dir.iterdir()
        if p.is_file() and p.suffix in (".pem", ".crt") and p.name != MERGED_CA_BUNDLE_NAME
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


def build_merged_ca_bundle(certs_dir: Path = CERTS_DIR) -> Path | None:
    """Build a merged CA bundle from certifi plus project certificates."""
    if not _ensure_certifi():
        return None

    import certifi

    cert_files = get_certificate_files(certs_dir)
    if not cert_files:
        Output.warn(f"No certificate files (.pem, .crt) found in {certs_dir}/")
        return None

    base_bundle = Path(certifi.where())
    merged_bundle = certs_dir / MERGED_CA_BUNDLE_NAME
    merged_content = base_bundle.read_bytes()
    added = 0

    for cert_path in cert_files:
        cert_data = cert_path.read_bytes().strip()
        if not cert_data:
            Output.warn(f"Skipping empty certificate file: {cert_path.name}")
            continue

        if cert_data in merged_content:
            Output.info(f"Certificate already present in bundle: {cert_path.name}")
            continue

        merged_content += b"\n" + cert_data + b"\n"
        Output.success(f"Added to merged bundle: {cert_path.name}")
        added += 1

    merged_bundle.write_bytes(merged_content)
    Output.info(f"Base CA bundle: {base_bundle}")
    Output.info(f"Merged CA bundle: {merged_bundle}")

    if added:
        Output.success(f"{added} certificate(s) added to merged CA bundle")
    else:
        Output.info("No new certificates were added (all already present)")

    return merged_bundle


def configure_certificate_env(bundle_path: Path, certs_dir: Path = CERTS_DIR) -> None:
    """Write certificate bundle paths into project env files if not already present."""
    try:
        bundle_value = bundle_path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        bundle_value = bundle_path.as_posix()

    try:
        certs_value = certs_dir.relative_to(Path.cwd()).as_posix()
    except ValueError:
        certs_value = certs_dir.as_posix()

    env_block = f"""
# Project certificate bundle
CERTS_PATH={certs_value}
REQUESTS_CA_BUNDLE={bundle_value}
SSL_CERT_FILE={bundle_value}
"""
    EnvManager.append_to_all(env_block, "REQUESTS_CA_BUNDLE")
    Output.info("Updated env files with CERTS_PATH, REQUESTS_CA_BUNDLE, and SSL_CERT_FILE")


def prepare_certificate_bundle(certs_dir: Path = CERTS_DIR, update_env: bool = True) -> Path | None:
    """Build the merged certificate bundle and optionally wire it into env files."""
    bundle_path = build_merged_ca_bundle(certs_dir)
    if bundle_path and update_env:
        configure_certificate_env(bundle_path, certs_dir)
    return bundle_path


@register
class InstallCertCommand(Command):
    signature = "install:cert"
    description = "Build a merged SSL CA bundle from project certificates"
    help = """
Examples:
  fastman install:cert

Place your .pem or .crt certificate files in the certs/ directory
at the root of your project, then run this command.
"""

    def handle(self):
        Output.info("Certificate Bundle Manager")
        Output.new_line()

        certs_dir = CERTS_DIR.resolve()
        Output.info(f"Certificates directory: {certs_dir}")

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
            Output.echo(f"  2. Run: fastman install:cert", Style.CYAN)
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

        # Show target CA bundle path
        try:
            import certifi
            Output.info(f"Base CA bundle: {certifi.where()}")
        except ImportError:
            Output.info("certifi not yet installed (will be installed automatically)")
        Output.new_line()

        bundle_path = prepare_certificate_bundle(certs_dir)
        if not bundle_path:
            return

        Output.new_line()
        Output.info("The merged CA bundle is ready for Python's requests/httpx/aiohttp libraries.")
        Output.info("Use REQUESTS_CA_BUNDLE / SSL_CERT_FILE to make external clients trust your project certificates.")
