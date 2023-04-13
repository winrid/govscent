This is the source code for govscent.org

### Dependencies

Govscent is a Django application.

- Python 3.10+
- PostgresSQL

### Setup

Django will automatically use an sqlite db in the project directory, so no DB or external service setup is required.

Once you get Django running, you'll want to create an admin user locally. Django has docs for this.

Then the admin panel is accessible via `http://localhost:8000/admin`.

You'll have to setup a `.env` file like the following:

```
ENV="dev"
SECRET_KEY="LOCAL_DEV"
OPENAI_API_ORG="org-abc"
OPENAI_API_KEY="sk-xyz"
DB_NAME="govscent"
DB_USER="postgres"
DB_PASSWORD="password"
DB_HOST="localhost"
DB_PORT="5432"
```

The OpenAPI keys are only required if you plan to run analysis from your machine.

#### Development DB

TODO - We will have an sqlite file you can download to get started with development quickly.

#### Data Flow

1. From Congress Data Sources.
2. → Then to On-Disk data structures (for now, may be removed in future to save disk space)
3. → Then to Local Database (SQLite locally, Postgresql in prod)
4. Analysis performed via cron and Python scripts.
5. Analysis results saved in Postgresql. We parse the response from GPT to extract the topic rating and topics list, and we also store the raw response, so it can be re-parsed without calling OpenAI.
6. Any errors from the API are also stored on the `Bill` for analysis and re-running later.
7. The `Bill` only contains the **raw text** as well as the response from the language model.
8. The pretty HTML version of the bill is generated at runtime via [govscentdotorg/services/bill_html_generator.py](govscentdotorg/services/bill_html_generator.py).
9. The pretty HTML is cached on disk for a short time to save CPU if a page goes viral. This saves significant disk space compared to saving millions of HTML or PDF files. 

#### CI

Merging to main will trigger a deployment. Deploys take around three seconds.

#### Scripts

Scripts are written using Django's RunScript plugin with the syntax `python3 manage.py runscript script_name --script-args arg_one arg_two`.

RunScript has its own docs, but arguments are passed via `--script-args`, and each arg is passed as an argument to the `run` method in your script.

Please type def your arguments. You can also mark them optional, like `def run(input_path: str | None)`

#### Getting Bills

1993 and onward bill data is from [github.com/unitedstates/congress](https://github.com/unitedstates/congress). You can run `usc-run govinfo --collections=BILLS --store=html` in that tool to get the data.

You'll then want to import the bills from the filesystem into the database. To keep things simple, each country will have its own import script, which is ran
via a cron in production.

For example, for USA: `python3 manage.py runscript usa_import_bills --script-args /congress-repo-path/data False False`.

#### Analyzing Bills

Bills can be analyzed via `python3 manage.py runscript analyze_bills --script-args False`. This scripts runs analysis sequentially. The cost is fairly low due to its
sequential nature, so it's fairly safe to run yourself.

Bulk analysis, done with each year in parallel, is available via the `analyze_bills_bulk` script. Be wary, this will rack up thousands of dollars very quickly.

#### Python?

There were concerns that Python would be too slow, but it has shown to be plenty fast enough. Most pages render < 10ms, and development productivity with type hints is good.
