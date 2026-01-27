# Changelog

## [2.1.1](https://github.com/canonical/identity-platform-login-ui-operator/compare/v2.1.0...v2.1.1) (2026-01-27)


### Bug Fixes

* check for leadership ([0ffc40d](https://github.com/canonical/identity-platform-login-ui-operator/commit/0ffc40df9c2f22f6bf7e0fd7fa627517757f61c8))
* remove deferred events ([0e6f62d](https://github.com/canonical/identity-platform-login-ui-operator/commit/0e6f62db8871031f82c4da206aaf7922a21daa86))

## [2.1.0](https://github.com/canonical/identity-platform-login-ui-operator/compare/v2.0.1...v2.1.0) (2026-01-09)


### Features

* add feature flags handling ([f44457e](https://github.com/canonical/identity-platform-login-ui-operator/commit/f44457e862cf8054d4567fc5e707be117c238158))


### Bug Fixes

* update OCI-image resource ([#376](https://github.com/canonical/identity-platform-login-ui-operator/issues/376)) ([71d72dd](https://github.com/canonical/identity-platform-login-ui-operator/commit/71d72dd8887d9379839679b224d4820f3d4e8efd))
* update OCI-image resource ([#390](https://github.com/canonical/identity-platform-login-ui-operator/issues/390)) ([a875760](https://github.com/canonical/identity-platform-login-ui-operator/commit/a875760c62ecf6daeeced981511022d0fa5c38f4))
* update oci-image to ghcr.io/canonical/identity-platform-login-ui:v0.24.1 ([2417554](https://github.com/canonical/identity-platform-login-ui-operator/commit/2417554a37cfcd83dc43a4c192d122ee74eb9a0f))
* update oci-image to ghcr.io/canonical/identity-platform-login-ui:v0.24.2 ([48e92fd](https://github.com/canonical/identity-platform-login-ui-operator/commit/48e92fd15a7cf92f5ccf5fe9b6d3c39215c06cae))

## [2.0.1](https://github.com/canonical/identity-platform-login-ui-operator/compare/v2.0.0...v2.0.1) (2025-11-17)


### Bug Fixes

* switch to use -route relation in the tf module ([7f9718a](https://github.com/canonical/identity-platform-login-ui-operator/commit/7f9718a8a0e7faba7b43928703f16bf9877316ac))
* update OCI-image resource ([#355](https://github.com/canonical/identity-platform-login-ui-operator/issues/355)) ([e92ff4b](https://github.com/canonical/identity-platform-login-ui-operator/commit/e92ff4b591b40d2742cc621ee6f1c130b3512cf3))
* update oci-image to ghcr.io/canonical/identity-platform-login-ui:v0.24.0 ([4319828](https://github.com/canonical/identity-platform-login-ui-operator/commit/43198280a6d81d45d73e9353b4a82c2dfc430d56))

## [2.0.0](https://github.com/canonical/identity-platform-login-ui-operator/compare/v1.2.0...v2.0.0) (2025-11-13)


### ⚠ BREAKING CHANGES

* add public-route and drop public and admin ingresses

### Features

* add public-route and drop public and admin ingresses ([52bd694](https://github.com/canonical/identity-platform-login-ui-operator/commit/52bd6947f71e21464370e15ba333c51058b8e837))


### Bug Fixes

* enable the charm resources in terraform module ([4c70a5c](https://github.com/canonical/identity-platform-login-ui-operator/commit/4c70a5cbb456fdb733a44817b6f02bacb8ea2221))
* enable the charm resources in terraform module ([fdff633](https://github.com/canonical/identity-platform-login-ui-operator/commit/fdff633a207b1e754c331bfeaf5c196b43f34e46))
* reinstate open_port method ([c37a140](https://github.com/canonical/identity-platform-login-ui-operator/commit/c37a140f845538f31d73ca139788f2a8040a1e50))
* update OCI-image resource ([b574a0a](https://github.com/canonical/identity-platform-login-ui-operator/commit/b574a0a801d8c95ceb01ffe15204ed82f1fc8418))
* update oci-image to ghcr.io/canonical/identity-platform-login-ui:v0.23.1 ([cefe3de](https://github.com/canonical/identity-platform-login-ui-operator/commit/cefe3deaaf4885018b70c49aec1e518f84448bc2))
* upgrade tf module to use 1.0.0 syntax ([5a834d5](https://github.com/canonical/identity-platform-login-ui-operator/commit/5a834d52fce2c8b6b62ba0b159fa6f8e751f6f60))

## [1.2.0](https://github.com/canonical/identity-platform-login-ui-operator/compare/v1.1.5...v1.2.0) (2025-10-02)


### Features

* update juju_application resource name ([baa5b1e](https://github.com/canonical/identity-platform-login-ui-operator/commit/baa5b1e6c3bb4332bcb3ea2157af535dd3f371d9))


### Bug Fixes

* make support email configurable ([6f4260c](https://github.com/canonical/identity-platform-login-ui-operator/commit/6f4260ce9abb918731143c11356466fdf79432de))
* remove the terraform state file ([20d72ce](https://github.com/canonical/identity-platform-login-ui-operator/commit/20d72ce7612c2bf6fa32b851315f8d33d00b465f))
* remove the terraform state file ([025e27d](https://github.com/canonical/identity-platform-login-ui-operator/commit/025e27d0ffb1102fa203978f9cd68e2cf8fcddf1))
* update OCI-image resource ([145c5dc](https://github.com/canonical/identity-platform-login-ui-operator/commit/145c5dc5ef1a18a9ad74e3888a491d58355589ee))
* update oci-image to ghcr.io/canonical/identity-platform-login-ui:v0.21.3 ([23e5669](https://github.com/canonical/identity-platform-login-ui-operator/commit/23e566930effea9ebf00223eec0d0dd919eac74d))
* use terraform module in deployment ([ae4c93d](https://github.com/canonical/identity-platform-login-ui-operator/commit/ae4c93d2840923b7a4b740b5461e005074ff06e5))

## [1.1.5](https://github.com/canonical/identity-platform-login-ui-operator/compare/v1.1.4...v1.1.5) (2025-07-11)


### Bug Fixes

* run holistic handler on update_status ([0e4dda5](https://github.com/canonical/identity-platform-login-ui-operator/commit/0e4dda525f0e54b46761ea137deb70feb963c1a0))
* update OCI-image resource ([162e8b6](https://github.com/canonical/identity-platform-login-ui-operator/commit/162e8b6e69696f1ceb6b0d0908a2ef68682f1be5))
* update oci-image to ghcr.io/canonical/identity-platform-login-ui:v0.21.2 ([83b9f19](https://github.com/canonical/identity-platform-login-ui-operator/commit/83b9f196078933c92b05ffc650f6fe9f75cc2469))
* use replan to restart the service ([c7286b8](https://github.com/canonical/identity-platform-login-ui-operator/commit/c7286b8a164eb304dc4a317367d431e7c13006ca))

## [1.1.4](https://github.com/canonical/identity-platform-login-ui-operator/compare/v1.1.3...v1.1.4) (2025-05-09)


### Bug Fixes

* fix constraint ([f91ce52](https://github.com/canonical/identity-platform-login-ui-operator/commit/f91ce52be64455bba07c7f1cf5f97054679ccb12))

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
