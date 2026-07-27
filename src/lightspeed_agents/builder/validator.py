class CompanyValidator:

    def validate(self, company):

        required = [
            "agents",
            "departments",
            "models",
            "workflows",
            "kpis",
        ]

        for section in required:

            if section not in company:
                raise ValueError(f"Missing configuration section: {section}")

            if company[section] is None:
                raise ValueError(f"Configuration section '{section}' is empty")

            if isinstance(company[section], (dict, list)) and len(company[section]) == 0:
                raise ValueError(f"Configuration section '{section}' contains no data")

        print("[OK] Configuration validated")

        return True
