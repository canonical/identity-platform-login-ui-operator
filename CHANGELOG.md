# Changelog

## 1.0.0 (2025-12-05)


### ⚠ BREAKING CHANGES

* add public-route and drop public and admin ingresses

### Features

* add public-route and drop public and admin ingresses ([52bd694](https://github.com/canonical/identity-platform-login-ui-operator/commit/52bd6947f71e21464370e15ba333c51058b8e837))
* add terraform module ([e31034e](https://github.com/canonical/identity-platform-login-ui-operator/commit/e31034e3fbb07e864f9333c69f956f77b8f4697b))
* send webauthn settings url in databag ([#184](https://github.com/canonical/identity-platform-login-ui-operator/issues/184)) ([0940ffb](https://github.com/canonical/identity-platform-login-ui-operator/commit/0940ffbe1ebb9a43f5466cfecd15cb49bd30c856))
* support oidc webauthn sequencing mode ([#177](https://github.com/canonical/identity-platform-login-ui-operator/issues/177)) ([9cc4f74](https://github.com/canonical/identity-platform-login-ui-operator/commit/9cc4f74b03ac1764eb4036d5bd84264bcf443549))
* update juju_application resource name ([baa5b1e](https://github.com/canonical/identity-platform-login-ui-operator/commit/baa5b1e6c3bb4332bcb3ea2157af535dd3f371d9))


### Bug Fixes

* add cert transfer integration ([6b78446](https://github.com/canonical/identity-platform-login-ui-operator/commit/6b784469dabb42b5fd006d5302dd724347edee4a))
* add constants file ([df7c058](https://github.com/canonical/identity-platform-login-ui-operator/commit/df7c0587e8de00ffed9bc0199a914fc799671cf3))
* add pod resource constraints ([715b9ee](https://github.com/canonical/identity-platform-login-ui-operator/commit/715b9ee1424028882a63173ee1d41ba662349a04))
* address CVEs ([e4d72c7](https://github.com/canonical/identity-platform-login-ui-operator/commit/e4d72c782cd4b3437f974fddc9830eb9c4fc6799)), closes [#231](https://github.com/canonical/identity-platform-login-ui-operator/issues/231)
* bump image to v0.24.1 to support hydra v25.4.0 ([30e42a8](https://github.com/canonical/identity-platform-login-ui-operator/commit/30e42a8c85c04dc2d88a910375a94ce1fb045e47))
* bump image to v0.24.1 to support hydra v25.4.0 ([#377](https://github.com/canonical/identity-platform-login-ui-operator/issues/377)) ([6d57439](https://github.com/canonical/identity-platform-login-ui-operator/commit/6d574392f49a43e851a2a0e920510ca820042950))
* bump ingress lib ([e764aa1](https://github.com/canonical/identity-platform-login-ui-operator/commit/e764aa13551430fdc385f14bcfbbaed89b3a7b3a))
* do not error if missing fields ([02f5157](https://github.com/canonical/identity-platform-login-ui-operator/commit/02f51579fec3d74ad13de8209aac37bbcada2aff))
* enable the charm resources in terraform module ([4c70a5c](https://github.com/canonical/identity-platform-login-ui-operator/commit/4c70a5cbb456fdb733a44817b6f02bacb8ea2221))
* enable the charm resources in terraform module ([fdff633](https://github.com/canonical/identity-platform-login-ui-operator/commit/fdff633a207b1e754c331bfeaf5c196b43f34e46))
* fix constraint ([f91ce52](https://github.com/canonical/identity-platform-login-ui-operator/commit/f91ce52be64455bba07c7f1cf5f97054679ccb12))
* fix the integration test dependency ([b1ba728](https://github.com/canonical/identity-platform-login-ui-operator/commit/b1ba728f78edf211a0441550bda05d4524d5a078))
* **loki-rule:** improve error handling in json parsing ([#99](https://github.com/canonical/identity-platform-login-ui-operator/issues/99)) ([cd8a5e0](https://github.com/canonical/identity-platform-login-ui-operator/commit/cd8a5e062c32f63530540027d756e4a43eb35029))
* make support email configurable ([6f4260c](https://github.com/canonical/identity-platform-login-ui-operator/commit/6f4260ce9abb918731143c11356466fdf79432de))
* pin dependencies ([570a51a](https://github.com/canonical/identity-platform-login-ui-operator/commit/570a51a059cf6d92cd6d95216448e50f7ad00139))
* provide optional flags in charmcraft.yaml ([b21e60d](https://github.com/canonical/identity-platform-login-ui-operator/commit/b21e60d504f30d6dd75198d975d0710ccb82db2b))
* reinstate open_port method ([c37a140](https://github.com/canonical/identity-platform-login-ui-operator/commit/c37a140f845538f31d73ca139788f2a8040a1e50))
* remove the terraform state file ([20d72ce](https://github.com/canonical/identity-platform-login-ui-operator/commit/20d72ce7612c2bf6fa32b851315f8d33d00b465f))
* remove the terraform state file ([025e27d](https://github.com/canonical/identity-platform-login-ui-operator/commit/025e27d0ffb1102fa203978f9cd68e2cf8fcddf1))
* run holistic handler on update_status ([0e4dda5](https://github.com/canonical/identity-platform-login-ui-operator/commit/0e4dda525f0e54b46761ea137deb70feb963c1a0))
* switch to use -route relation in the tf module ([7f9718a](https://github.com/canonical/identity-platform-login-ui-operator/commit/7f9718a8a0e7faba7b43928703f16bf9877316ac))
* **test:** after refactor ([d969fbd](https://github.com/canonical/identity-platform-login-ui-operator/commit/d969fbd8ab15b0e75d3908a9aff7d3a2758be322))
* update integration-requirements.txt ([ab96656](https://github.com/canonical/identity-platform-login-ui-operator/commit/ab966562bcee50b66392a16905c960adf689ce3e))
* update integration-requirements.txt ([efc2155](https://github.com/canonical/identity-platform-login-ui-operator/commit/efc2155ddd79877d8a0dcfefa652004a92457e16))
* update login_ui_endpoints lib ([d923498](https://github.com/canonical/identity-platform-login-ui-operator/commit/d923498e5ac2deee3fc287dfc74b3f82fac025fe))
* update OCI-image resource ([b574a0a](https://github.com/canonical/identity-platform-login-ui-operator/commit/b574a0a801d8c95ceb01ffe15204ed82f1fc8418))
* update OCI-image resource ([145c5dc](https://github.com/canonical/identity-platform-login-ui-operator/commit/145c5dc5ef1a18a9ad74e3888a491d58355589ee))
* update OCI-image resource ([162e8b6](https://github.com/canonical/identity-platform-login-ui-operator/commit/162e8b6e69696f1ceb6b0d0908a2ef68682f1be5))
* update OCI-image resource ([#355](https://github.com/canonical/identity-platform-login-ui-operator/issues/355)) ([e92ff4b](https://github.com/canonical/identity-platform-login-ui-operator/commit/e92ff4b591b40d2742cc621ee6f1c130b3512cf3))
* update oci-image to ghcr.io/canonical/identity-platform-login-ui:v0.21.2 ([83b9f19](https://github.com/canonical/identity-platform-login-ui-operator/commit/83b9f196078933c92b05ffc650f6fe9f75cc2469))
* update oci-image to ghcr.io/canonical/identity-platform-login-ui:v0.21.3 ([23e5669](https://github.com/canonical/identity-platform-login-ui-operator/commit/23e566930effea9ebf00223eec0d0dd919eac74d))
* update oci-image to ghcr.io/canonical/identity-platform-login-ui:v0.23.1 ([cefe3de](https://github.com/canonical/identity-platform-login-ui-operator/commit/cefe3deaaf4885018b70c49aec1e518f84448bc2))
* update oci-image to ghcr.io/canonical/identity-platform-login-ui:v0.24.0 ([4319828](https://github.com/canonical/identity-platform-login-ui-operator/commit/43198280a6d81d45d73e9353b4a82c2dfc430d56))
* upgrade tf module to use 1.0.0 syntax ([5a834d5](https://github.com/canonical/identity-platform-login-ui-operator/commit/5a834d52fce2c8b6b62ba0b159fa6f8e751f6f60))
* use replan to restart the service ([c7286b8](https://github.com/canonical/identity-platform-login-ui-operator/commit/c7286b8a164eb304dc4a317367d431e7c13006ca))
* use terraform module in deployment ([ae4c93d](https://github.com/canonical/identity-platform-login-ui-operator/commit/ae4c93d2840923b7a4b740b5461e005074ff06e5))
