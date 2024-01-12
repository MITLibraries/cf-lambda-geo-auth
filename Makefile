SHELL=/bin/bash
DATETIME:=$(shell date -u +%Y%m%dT%H%M%SZ)

help: # preview Makefile commands
	@awk 'BEGIN { FS = ":.*#"; print "Usage:  make <target>\n\nTargets:" } \
/^[-_[:alpha:]]+:.?*#/ { printf "  %-15s%s\n", $$1, $$2 }' $(MAKEFILE_LIST)

## ---- Dependency commands ---- ##

install: # install Python dependencies
	pipenv install --dev
	pipenv run pre-commit install

update: install # update Python dependencies
	pipenv clean
	pipenv update --dev

## ---- Unit test commands ---- ##

test: # run tests and print a coverage report
	pipenv run coverage run --source=lambdas -m pytest -vv
	pipenv run coverage report -m

coveralls: test # write coverage data to an LCOV report
	pipenv run coverage lcov -o ./coverage/lcov.info

## ---- Code quality and safety commands ---- ##

lint: black mypy ruff safety # run linters

black: # run 'black' linter and print a preview of suggested changes
	pipenv run black --check --diff .

mypy: # run 'mypy' linter
	pipenv run mypy .

ruff: # run 'ruff' linter and print a preview of errors
	pipenv run ruff check .

safety: # check for security vulnerabilities and verify Pipfile.lock is up-to-date
	pipenv check
	pipenv verify

lint-apply: # apply changes with 'black' and resolve 'fixable errors' with 'ruff'
	black-apply ruff-apply 

black-apply: # apply changes with 'black'
	pipenv run black .

ruff-apply: # resolve 'fixable errors' with 'ruff'
	pipenv run ruff check --fix .

##   Terraform Generated Makefile Additions                                   ##
##   ---- Local Developer Deployment Commands ----                            ##

# It is expected that the `create-zip` command is updated by the 
# developer to match the needs of the application. This is just 
# the default zip method for a very simple function.
create-zip: # Create a .zip file of code
	rm -rf cf-lambda-geo-auth.py.zip
	zip -j cf-lambda-geo-auth.py.zip lambdas/*

upload-zip: # Upload the .zip file to AWS S3 bucket
	aws s3api put-object --bucket shared-files-$$(aws sts get-caller-identity --query Account --output text) --body cf-lambda-geo-auth.py.zip --key files/cf-lambda-geo-auth.py.zip

##  End of Terraform Generated Makefile Additions                             ##
