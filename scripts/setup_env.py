"""Create/sync local env files without replacing existing configuration values."""
from pathlib import Path
import secrets
from dotenv import dotenv_values

root = Path(__file__).resolve().parents[1]
for directory in ('backend', 'frontend'):
    target = root / directory / '.env'
    if not target.exists():
        target.write_text(target.with_name('.env.example').read_text(encoding='utf-8'), encoding='utf-8')
    else:
        existing = dotenv_values(target)
        template = target.with_name('.env.example').read_text(encoding='utf-8')
        missing = [line for line in template.splitlines()
                   if line and not line.startswith('#') and '=' in line and line.split('=', 1)[0] not in existing]
        if missing:
            with target.open('a', encoding='utf-8') as stream:
                stream.write('\n# Additional defaults; existing values are preserved.\n' + '\n'.join(missing) + '\n')
    if directory == 'backend':
        text = target.read_text(encoding='utf-8')
        placeholder = 'replace-with-a-random-secret-at-least-32-characters'
        if placeholder in text:
            target.write_text(text.replace(placeholder, secrets.token_urlsafe(48)), encoding='utf-8')
print('Local configuration ready; existing values preserved and secrets not printed.')
