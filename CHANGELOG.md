# Changelog

## [1.1.3](https://github.com/canonical/identity-platform-login-ui-operator/compare/v1.1.2...v1.1.3) (2025-05-09)


### Bug Fixes

* add pod resource constraints ([715b9ee](https://github.com/canonical/identity-platform-login-ui-operator/commit/715b9ee1424028882a63173ee1d41ba662349a04))
* **test:** after refactor ([d969fbd](https://github.com/canonical/identity-platform-login-ui-operator/commit/d969fbd8ab15b0e75d3908a9aff7d3a2758be322))

## [1.1.2](https://github.com/canonical/identity-platform-login-ui-operator/compare/v1.1.1...v1.1.2) (2025-04-08)


### Bug Fixes

* bump ingress lib ([e764aa1](https://github.com/canonical/identity-platform-login-ui-operator/commit/e764aa13551430fdc385f14bcfbbaed89b3a7b3a))
* update login_ui_endpoints lib ([d923498](https://github.com/canonical/identity-platform-login-ui-operator/commit/d923498e5ac2deee3fc287dfc74b3f82fac025fe))

## [1.1.1](https://github.com/canonical/identity-platform-login-ui-operator/compare/v1.1.0...v1.1.1) (2025-04-01)


### Bug Fixes

* address CVEs ([e4d72c7](https://github.com/canonical/identity-platform-login-ui-operator/commit/e4d72c782cd4b3437f974fddc9830eb9c4fc6799)), closes [#231](https://github.com/canonical/identity-platform-login-ui-operator/issues/231)
* do not error if missing fields ([02f5157](https://github.com/canonical/identity-platform-login-ui-operator/commit/02f51579fec3d74ad13de8209aac37bbcada2aff))

## [1.1.0](https://github.com/canonical/identity-platform-login-ui-operator/compare/v1.0.1...v1.1.0) (2025-03-25)


### Features

* add terraform module ([e31034e](https://github.com/canonical/identity-platform-login-ui-operator/commit/e31034e3fbb07e864f9333c69f956f77b8f4697b))


### Bug Fixes

* fix the integration test dependency ([b1ba728](https://github.com/canonical/identity-platform-login-ui-operator/commit/b1ba728f78edf211a0441550bda05d4524d5a078))
* provide optional flags in charmcraft.yaml ([b21e60d](https://github.com/canonical/identity-platform-login-ui-operator/commit/b21e60d504f30d6dd75198d975d0710ccb82db2b))

## [1.0.1](https://github.com/canonical/identity-platform-login-ui-operator/compare/v1.0.0...v1.0.1) (2025-03-05)


### Bug Fixes

* pin dependencies ([570a51a](https://github.com/canonical/identity-platform-login-ui-operator/commit/570a51a059cf6d92cd6d95216448e50f7ad00139))

## 1.0.0 (2025-03-05)


### Features

* Added publish and release workflows to .github/workflows. Modified on_push.yaml to incorporate publishing. Modified on_schedule, renovate, and update_libs yaml files to be consistent with the other identity stack repositories. ([7876a7e](https://github.com/canonical/identity-platform-login-ui-operator/commit/7876a7e0af9431fbb0a0e067c035bce72066e498))
* Added workflow to unit test charm on PR ([d313260](https://github.com/canonical/identity-platform-login-ui-operator/commit/d31326035971c014a2208d27e540e2ae069f2c7c))
* implement tempo integration and feed it to otel env vars ([9bcfdff](https://github.com/canonical/identity-platform-login-ui-operator/commit/9bcfdffcd10901a20bd407fd307f4c74503a4b06))
* install tempo-k8s lib ([3c9ae85](https://github.com/canonical/identity-platform-login-ui-operator/commit/3c9ae85feb4955bf706045b7555a88b171c5f0d5))
* send webauthn settings url in databag ([#184](https://github.com/canonical/identity-platform-login-ui-operator/issues/184)) ([0940ffb](https://github.com/canonical/identity-platform-login-ui-operator/commit/0940ffbe1ebb9a43f5466cfecd15cb49bd30c856))
* support oidc webauthn sequencing mode ([#177](https://github.com/canonical/identity-platform-login-ui-operator/issues/177)) ([9cc4f74](https://github.com/canonical/identity-platform-login-ui-operator/commit/9cc4f74b03ac1764eb4036d5bd84264bcf443549))


### Bug Fixes

* add cert transfer integration ([6b78446](https://github.com/canonical/identity-platform-login-ui-operator/commit/6b784469dabb42b5fd006d5302dd724347edee4a))
* add constants file ([df7c058](https://github.com/canonical/identity-platform-login-ui-operator/commit/df7c0587e8de00ffed9bc0199a914fc799671cf3))
* add on_install for log dir creation ([aaf49df](https://github.com/canonical/identity-platform-login-ui-operator/commit/aaf49dfa8826ec3dfc99dd4500b1d821b859d622))
* Added configuration files renovate.json and renovate-config.js for renovate.yaml github action. ([0e732fd](https://github.com/canonical/identity-platform-login-ui-operator/commit/0e732fd0865a478fd969561779a149a08341291e))
* Added fixes to metadata.yaml and charm.py ([c33baba](https://github.com/canonical/identity-platform-login-ui-operator/commit/c33baba0fbc098f5656bde74825d2d73b4889304))
* Added workflows from Hydra Operator. Publishing workflows will be added when the operator is approved for publishing. ([e4ae310](https://github.com/canonical/identity-platform-login-ui-operator/commit/e4ae3106c4b5673e59957c5f958755e0f030c9ab))
* Applied fixes to unit tests ([7c388ed](https://github.com/canonical/identity-platform-login-ui-operator/commit/7c388ed595682ce86b9986d1107216f71492f529))
* change command binary ([545e395](https://github.com/canonical/identity-platform-login-ui-operator/commit/545e3959dd7f8d66800966ffb63778d1bc587a75))
* change prometheus endpoint and add extra env vars for tracing and logging ([e2c9bbd](https://github.com/canonical/identity-platform-login-ui-operator/commit/e2c9bbda9226128c81b32830874c3d86a82fb9be))
* Changed charming-actions to current latest release ([5c0598c](https://github.com/canonical/identity-platform-login-ui-operator/commit/5c0598c3082d5682741deb320ea541ec0f286f58))
* Fixed comments in PR [#2](https://github.com/canonical/identity-platform-login-ui-operator/issues/2). ([315cbb3](https://github.com/canonical/identity-platform-login-ui-operator/commit/315cbb3892e12468f69a407e102dd1462f5452c5))
* Fixed image uploading issue ([2d5105a](https://github.com/canonical/identity-platform-login-ui-operator/commit/2d5105a353d12a4f8a7b4b31aaa3394b41cc01e3))
* fixed linting on tests/unit/conftest.py ([59917a6](https://github.com/canonical/identity-platform-login-ui-operator/commit/59917a67b2cdf7c2c15f3597d0c1c9f76c574246))
* Fixed release versions in invocations of canonical/charming-actions ([40f5176](https://github.com/canonical/identity-platform-login-ui-operator/commit/40f5176dcb6e9b5af77bd59c19b950d10083338d))
* Fixed the last unresolved comments in PR [#2](https://github.com/canonical/identity-platform-login-ui-operator/issues/2). Took out unused functions from charm.py. Changed Usage section in README.md ([9022fac](https://github.com/canonical/identity-platform-login-ui-operator/commit/9022fac1a79e61e1405c1281028be7d3372a20cf))
* Fixes according to requests on PR [#2](https://github.com/canonical/identity-platform-login-ui-operator/issues/2) ([6030d71](https://github.com/canonical/identity-platform-login-ui-operator/commit/6030d7105f875a57c3ae921f577a43c38f80f20f))
* Fixes for comments in PR [#2](https://github.com/canonical/identity-platform-login-ui-operator/issues/2) ([58d6403](https://github.com/canonical/identity-platform-login-ui-operator/commit/58d6403434f33a0be635fb389092419a95bff169))
* Fixing comments in PR [#2](https://github.com/canonical/identity-platform-login-ui-operator/issues/2). Change method name, and correct comment in charm.py. Corrected documentation in CONTRIBUTING.md ([fc8dcfe](https://github.com/canonical/identity-platform-login-ui-operator/commit/fc8dcfe6b15b85e5c4dee78d154c66a472a4c3f0))
* Fixing linting issues ([ec8bc9d](https://github.com/canonical/identity-platform-login-ui-operator/commit/ec8bc9d2b50ee8fce596c574e9be6eb6a2509f8d))
* Fixing naming and network bugs in charm ([0aa50d6](https://github.com/canonical/identity-platform-login-ui-operator/commit/0aa50d637a809fdaad37ae2ec4256e640bb5ea78))
* Fixing PR based on comments ([dd44224](https://github.com/canonical/identity-platform-login-ui-operator/commit/dd44224b69a35d09b212ba02d2ab4f0c5b72d0f7))
* introduce tracing_enabled config var ([94b9b01](https://github.com/canonical/identity-platform-login-ui-operator/commit/94b9b011fa37a3d11463576a22dc18a9e3f8ed86))
* Last minute change for deployment section in CONTRIBUTING.md. ([500edc3](https://github.com/canonical/identity-platform-login-ui-operator/commit/500edc3e4d26aa430de20b1d675a856babdeee84))
* Linting fix for charm.py and test_charm.py ([53e7451](https://github.com/canonical/identity-platform-login-ui-operator/commit/53e74510dd50e264e00ee8f35091681c020fded7))
* **loki-rule:** improve error handling in json parsing ([#99](https://github.com/canonical/identity-platform-login-ui-operator/issues/99)) ([cd8a5e0](https://github.com/canonical/identity-platform-login-ui-operator/commit/cd8a5e062c32f63530540027d756e4a43eb35029))
* pin container image ([16d9217](https://github.com/canonical/identity-platform-login-ui-operator/commit/16d92176fcde75caa90bc3afbbbd27116558ed65))
* pin image version to stable ([879dbfc](https://github.com/canonical/identity-platform-login-ui-operator/commit/879dbfcd5778aba8d4d7e928bd6ccc05060e962c))
* Possible fix for the problem with the publish workflow. This is for a draft PR ([8644dc2](https://github.com/canonical/identity-platform-login-ui-operator/commit/8644dc2df35e67ae8b06d2e146c5710c92ece8a8))
* PR [#1](https://github.com/canonical/identity-platform-login-ui-operator/issues/1) fixes ([2c1f2cd](https://github.com/canonical/identity-platform-login-ui-operator/commit/2c1f2cdc3fca016f6da84a73b8be22a85a9ea650))
* swap healthcheck endpoint ([7fdb79b](https://github.com/canonical/identity-platform-login-ui-operator/commit/7fdb79b310b5d1b940e9646b3714f3def620a3de))
* update integration-requirements.txt ([efc2155](https://github.com/canonical/identity-platform-login-ui-operator/commit/efc2155ddd79877d8a0dcfefa652004a92457e16))
* use strings for paths ([2341d0f](https://github.com/canonical/identity-platform-login-ui-operator/commit/2341d0f11036fdfa1f8997a87a1b63f8081b6d28))
