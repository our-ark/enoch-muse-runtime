# Contributing

Keep changes scoped to the provider contract, mailbox transport or managed
instance lifecycle. Run the suite in the [development guide](docs/development.md#offline-checks)
against the documented Enoch revision and include the relevant checks with a
pull request.

Use isolated synthetic state in tests and research records. Never commit live
mailboxes, production agent state, `.env` files or credentials. Do not edit
historical experiment records to make a check pass: record corrections or
additional analysis separately and retain the original evidence.

New contributions are made under the Apache-2.0 license. Report bugs with a
minimal synthetic example and the adapter/body revisions, without private
prompts or credentials. No model account is needed for the automated tests.
