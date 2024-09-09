# This is the default recipe when no arguments are provided
[private]
current_version := `grep 'version' pyproject.toml | cut -d '"' -f 2`
tag_name        := "v" + current_version

default:
  @just --list --unsorted

test *FLAGS:
  uv run pytest tests -m "not integration" {{FLAGS}}

integration *FLAGS:
  uv run pytest tests -m integration {{FLAGS}}

format:
  uvx ruff check . --fix
  uvx ruff format .

coverage *FLAGS:
  uv run coverage run -m pytest tests -m "not integration" {{FLAGS}}
  uv run coverage report
  uv run coverage lcov -o lcov.info

ai-exchange-version:
  curl -s https://pypi.org/pypi/ai-exchange/json | jq -r .info.version

# bump project version, push, create pr
release version:
  uvx --from=toml-cli toml set --toml-path=pyproject.toml project.version {{version}}
  ai_exchange_version=$(just ai-exchange-version) && sed -i '' 's/ai-exchange>=.*/ai-exchange>='"${ai_exchange_version}"'\",/' pyproject.toml
  git co -b release-version-{{version}}
  git add .
  git commit -m "chore(release): release version {{version}}"

tag:
  git tag {{tag_name}}

# this will kick of ci for release
# use this when release branch is merged to main
tag-push:
  just tag
  git push origin tag {{tag_name}}
