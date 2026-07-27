from lightspeed_agents.builder.loader import CompanyLoader
from lightspeed_agents.builder.validator import CompanyValidator
from lightspeed_agents.builder.generator import CompanyGenerator
from lightspeed_agents.builder.writer import CompanyWriter


class CompanyBuilder:

    def __init__(
        self,
        config_dir: str = "company",
        output_dir: str = ".opencode",
        dry_run: bool = False,
    ):
        self.config_dir = config_dir
        self.output_dir = output_dir
        self.dry_run = dry_run

    def run(self):

        print("Loading company configuration...")

        company = CompanyLoader(self.config_dir).load()

        print("Validating configuration...")

        CompanyValidator().validate(company)

        print("Generating company assets...")

        assets = CompanyGenerator().generate(company)

        if self.dry_run:
            print("DRY RUN: no files were written")
            return assets

        print("Writing OpenCode structure...")

        CompanyWriter(self.output_dir).write(assets)

        print("Company successfully built.")

        return assets
