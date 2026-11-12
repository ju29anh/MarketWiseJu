"""Snapshot the installed runtime dependency closure, without unrelated machine packages."""
from importlib.metadata import distribution
from pathlib import Path
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

root = Path(__file__).resolve().parents[1]
pending = [Requirement(line).name for line in (root / 'backend/requirements.txt').read_text().splitlines() if line and not line.startswith('#')]
resolved = {}
while pending:
    name = canonicalize_name(pending.pop())
    if name in resolved:
        continue
    package = distribution(name)
    resolved[name] = package.version
    for line in package.requires or []:
        requirement = Requirement(line)
        if requirement.marker is None or requirement.marker.evaluate({'extra': ''}):
            pending.append(requirement.name)
(root / 'backend/requirements-lock.txt').write_text(
    '# Runtime versions tested on Windows / Python 3.13. Regenerate after reviewed upgrades.\n' +
    '\n'.join(f'{name}=={version}' for name, version in sorted(resolved.items())) + '\n', encoding='utf-8')
print(f'Locked {len(resolved)} runtime packages.')
