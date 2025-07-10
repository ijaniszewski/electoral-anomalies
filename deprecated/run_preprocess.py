import click
import inquirer
import importlib


@click.command()
def main():
    """
    Interactive CLI to run preprocessing based on user selection.
    """
    click.echo("#" * 60)
    click.echo("\U0001f9fe  Electoral Data Preprocessing")
    click.echo("-" * 60)

    # Prompt: country, year, election, round
    country = inquirer.prompt(
        [
            inquirer.List(
                "country",
                message="Select country",
                choices=["poland"],
                default="poland",
            )
        ]
    )["country"]

    year = inquirer.prompt(
        [inquirer.List("year", message="Select year", choices=["2025"], default="2025")]
    )["year"]

    election = inquirer.prompt(
        [
            inquirer.List(
                "election",
                message="Select election type",
                choices=["presidential"],
                default="presidential",
            )
        ]
    )["election"]

    round_input = inquirer.prompt(
        [
            inquirer.List(
                "round",
                message="Select round",
                choices=["round1", "round2", "none"],
                default="round2",
            )
        ]
    )["round"]
    round_value = None if round_input == "none" else round_input

    # Prompt: file name
    file_name = inquirer.prompt(
        [
            inquirer.Text(
                "file_name",
                message="Enter input CSV file name",
                default=f"{year}_{election}_{round_input}.csv",
            )
        ]
    )["file_name"]

    # Construct module path
    module_path = f"src.preprocess.{country}_{year}_{election}"

    try:
        module = importlib.import_module(module_path)
    except ModuleNotFoundError:
        click.echo(f"❌ Could not find module: {module_path}")
        return

    if not hasattr(module, "process_df"):
        click.echo(f"❌ Module {module_path} has no function 'process_df'")
        return

    # Run preprocess function with arguments
    click.echo(
        f"✅ Running {module_path}.process_df(file_name='{file_name}', round='{round_value}')"
    )
    df = module.process_df(file_name=file_name, round=round_value)

    if hasattr(module, "save_processed"):
        module.save_processed(df, file_name)
        click.echo("✅ Saved cleaned CSV.")
    else:
        click.echo(df.head())


if __name__ == "__main__":
    main()
