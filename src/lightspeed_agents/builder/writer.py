from pathlib import Path
import json


class CompanyWriter:

    def __init__(self, output_dir: str = '.opencode'):
        self.output_dir = Path(output_dir)

    def write(self, assets):

        self._create_structure()
        self._write_agents(assets['agents'])
        self._write_inbox()
        self._write_summary(assets)

        print('OpenCode assets written.')

    def _create_structure(self):

        directories = [
            self.output_dir,
            self.output_dir / 'agents',
            self.output_dir / 'config',
            self.output_dir / 'memory',
            self.output_dir / 'knowledge',
            self.output_dir / 'projects',
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def _write_agents(self, agents):

        for agent in agents:

            path = self.output_dir / 'agents' / f'{agent["id"]}.md'

            content = f'''# {agent["name"]}

## Role
{agent["role"]}

## Department
{agent["department"]}

## Reports To
{agent["reportsTo"]}

## Tools
{", ".join(agent["tools"])}

## Permissions
{", ".join(agent["permissions"])}
'''

            path.write_text(content, encoding='utf-8')

    def _write_inbox(self):

        inbox = self.output_dir / 'inbox.json'

        if not inbox.exists():
            inbox.write_text('[]', encoding='utf-8')

    def _write_summary(self, assets):

        summary = {
            'agent_count': len(assets['agents']),
            'department_count': len(
                assets['departments'].get('departments', [])
            ),
        }

        path = self.output_dir / 'config' / 'summary.json'

        path.write_text(
            json.dumps(summary, indent=2),
            encoding='utf-8'
        )
