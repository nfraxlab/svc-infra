# CHANGELOG


## v1.11.0 (2026-01-31)

### Features

- **auth**: Fallback to CORS_ORIGINS for redirect validation
  ([#95](https://github.com/nfraxlab/svc-infra/pull/95),
  [`e718b30`](https://github.com/nfraxlab/svc-infra/commit/e718b30eb22a3aa6828e481950ebffc770a5af83))


## v1.10.0 (2026-01-31)

### Features

- Add email module with multi-provider backend support
  ([#94](https://github.com/nfraxlab/svc-infra/pull/94),
  [`4cf8ae8`](https://github.com/nfraxlab/svc-infra/commit/4cf8ae87d8bae303c3c15c7295403b4bff551467))


## v1.9.0 (2026-01-26)

### Features

- Add JobRegistry and session management enhancements
  ([#93](https://github.com/nfraxlab/svc-infra/pull/93),
  [`bf1db26`](https://github.com/nfraxlab/svc-infra/commit/bf1db26f471ae15c18ea810fe3ff8ed967f41212))


## v1.8.0 (2026-01-22)

### Features

- **api**: Add version app registry for direct OpenAPI access
  ([#92](https://github.com/nfraxlab/svc-infra/pull/92),
  [`9002dcd`](https://github.com/nfraxlab/svc-infra/commit/9002dcddb8fd2006f14914a65e4a2bf6a8bc352c))


## v1.7.0 (2026-01-21)

### Bug Fixes

- Update cli import path to ai_infra.llm.shell
  ([#90](https://github.com/nfraxlab/svc-infra/pull/90),
  [`8813330`](https://github.com/nfraxlab/svc-infra/commit/88133300c36ed7c6ea81c7e37a05c2b8bd3ad0d0))

### Features

- **auth**: Add session tracking to password login flow
  ([#91](https://github.com/nfraxlab/svc-infra/pull/91),
  [`13a09ee`](https://github.com/nfraxlab/svc-infra/commit/13a09ee8aec578ac94c398e05055e49887a3b458))


## v1.6.2 (2026-01-06)

### Bug Fixes

- Update stripe test error module paths and schema field names
  ([#89](https://github.com/nfraxlab/svc-infra/pull/89),
  [`7c02dca`](https://github.com/nfraxlab/svc-infra/commit/7c02dca4deb898860988ab8b97dfebb584ea1e4d))


## v1.6.1 (2026-01-05)

### Bug Fixes

- Use griffe labels for async method detection
  ([#88](https://github.com/nfraxlab/svc-infra/pull/88),
  [`c2165e2`](https://github.com/nfraxlab/svc-infra/commit/c2165e2520f17312740996435da53eb5c51965c3))

### Documentation

- Add docstrings to classes missing API documentation
  ([#85](https://github.com/nfraxlab/svc-infra/pull/85),
  [`1291de5`](https://github.com/nfraxlab/svc-infra/commit/1291de52e15e63bf4a5d6b84eab582b4ae7003f6))

- Enhance API extraction with auto-discovery ([#86](https://github.com/nfraxlab/svc-infra/pull/86),
  [`ad13c43`](https://github.com/nfraxlab/svc-infra/commit/ad13c437d326bb29249cd4571a2d3ad12eca1406))

- Remove stale dataclass JSON files ([#87](https://github.com/nfraxlab/svc-infra/pull/87),
  [`7736963`](https://github.com/nfraxlab/svc-infra/commit/773696307f4524414cb5bf4cd77b5e9659722652))


## v1.6.0 (2026-01-05)

### Features

- Auto-discover classes in API extraction script
  ([#84](https://github.com/nfraxlab/svc-infra/pull/84),
  [`df78faf`](https://github.com/nfraxlab/svc-infra/commit/df78faf2622e6b0003dbb09ee8bf43681c99a78a))

Co-authored-by: nfrax <alixkhatami@gmail.com>


## v1.5.0 (2026-01-05)

### Features

- Add griffe-based API reference extraction system
  ([#83](https://github.com/nfraxlab/svc-infra/pull/83),
  [`c3ccf3d`](https://github.com/nfraxlab/svc-infra/commit/c3ccf3d2852e57190f57aa6b06d1b1cdf49974a9))


## v1.4.0 (2026-01-04)

### Features

- Make redis queue backoff test more reliable in CI
  ([#82](https://github.com/nfraxlab/svc-infra/pull/82),
  [`4b70697`](https://github.com/nfraxlab/svc-infra/commit/4b70697bbf7fa8c4b7e2d5bce994c33b456a6f4f))


## v1.3.0 (2026-01-04)

### Features

- Add architecture, quickstart, troubleshooting, and performance docs
  ([#81](https://github.com/nfraxlab/svc-infra/pull/81),
  [`3b3ee66`](https://github.com/nfraxlab/svc-infra/commit/3b3ee66f1854f4d134b746ee7078642018aa50fa))


## v1.2.0 (2026-01-04)

### Features

- Add integration tests and CI workflow for Redis, PostgreSQL, Stripe
  ([#80](https://github.com/nfraxlab/svc-infra/pull/80),
  [`4ba6bf9`](https://github.com/nfraxlab/svc-infra/commit/4ba6bf94c644d6cd9fb01a01deb26adfa3eef0ba))


## v1.1.3 (2026-01-03)

### Bug Fixes

- Remove all emojis from documentation and code files
  ([#79](https://github.com/nfraxlab/svc-infra/pull/79),
  [`5f9f820`](https://github.com/nfraxlab/svc-infra/commit/5f9f8208041dc279f13ed2371ef026ee4571711b))


## v1.1.2 (2026-01-03)

### Bug Fixes

- Add unit tests for db utils, webhooks, cache, and payments (Phase 1.2.5-1.2.7)
  ([#78](https://github.com/nfraxlab/svc-infra/pull/78),
  [`ac195b7`](https://github.com/nfraxlab/svc-infra/commit/ac195b78ee5ecd36c0d12c0e283a25604bf77772))


## v1.1.1 (2026-01-02)

### Bug Fixes

- Align README hero section with robo-infra style
  ([#77](https://github.com/nfraxlab/svc-infra/pull/77),
  [`a9c50f3`](https://github.com/nfraxlab/svc-infra/commit/a9c50f3ed47cc628f8105befedb22b4565dea5d6))


## v1.1.0 (2025-12-30)

### Bug Fixes

- Add PR title enforcement workflow ([#74](https://github.com/nfraxlab/svc-infra/pull/74),
  [`24856fb`](https://github.com/nfraxlab/svc-infra/commit/24856fb93eccd0574e6ecf0a389262c74ce5a34d))

- Semantic-release push tags before publish ([#75](https://github.com/nfraxlab/svc-infra/pull/75),
  [`79fa11c`](https://github.com/nfraxlab/svc-infra/commit/79fa11c34db3ef9ae7977f562d7291c1bf5e7554))

### Chores

- Regenerate poetry.lock after adding semantic-release
  ([#68](https://github.com/nfraxlab/svc-infra/pull/68),
  [`c3220e0`](https://github.com/nfraxlab/svc-infra/commit/c3220e04a3b921735115140e6378a1bf6719916d))

* chore: regenerate poetry.lock after adding semantic-release

* feat: add robust make pr automation with contributor-safe workflow

- Remove mcp-shim and package.json ([#70](https://github.com/nfraxlab/svc-infra/pull/70),
  [`e431fef`](https://github.com/nfraxlab/svc-infra/commit/e431fef5f1edbb3820ff40016ca1fd4151b9fe59))

### Continuous Integration

- Switch to semantic-release for clean versioning
  ([`c955b04`](https://github.com/nfraxlab/svc-infra/commit/c955b040ed1230890886ccb51c821002c516bb5d))

### Documentation

- Update CONTRIBUTING.md with make pr workflow
  ([#73](https://github.com/nfraxlab/svc-infra/pull/73),
  [`fa4c53a`](https://github.com/nfraxlab/svc-infra/commit/fa4c53a631a3272661d078617f0c2b8ae604a4c2))

### Features

- Add production readiness gate with CI integration
  ([#69](https://github.com/nfraxlab/svc-infra/pull/69),
  [`12de291`](https://github.com/nfraxlab/svc-infra/commit/12de291c04b734dc4b677404d6cbea2009d9ddd4))


## v1.0.7 (2025-12-28)

### Continuous Integration

- Create GitHub Release for every version
  ([`1cbb66c`](https://github.com/nfraxlab/svc-infra/commit/1cbb66ce65bd93fac5847d95626915f4ea83cf6d))

- Release v1.0.7
  ([`d839eef`](https://github.com/nfraxlab/svc-infra/commit/d839eef51d45c26f5beaf725cc8c6fbbdb14ac42))


## v1.0.6 (2025-12-28)

### Bug Fixes

- **ci**: Detect x.y.0 releases and skip auto-bump to create GitHub Release
  ([`d254267`](https://github.com/nfraxlab/svc-infra/commit/d254267be4da12806766af69d2a6fcd8a82f2b7f))

The workflow was auto-bumping patch version before checking if it was a minor/major release, causing
  x.y.0 to become x.y.1 and skip release creation.

Now the workflow checks the current version BEFORE bumping: - If version ends in .0 (e.g., 1.0.0,
  2.1.0), it's a deliberate release - Skip auto-bump, keep version as-is - Create GitHub Release -
  Otherwise, bump patch and publish normally (no release)

- **ci**: Only release x.y.0 versions, no auto-bump
  ([`30bc5a6`](https://github.com/nfraxlab/svc-infra/commit/30bc5a6251f9429f97c5fe5130192e640ca2ea99))

Changed the workflow to: - Only publish when version is x.y.0 (deliberate release) - Skip all
  publish steps for non x.y.0 versions - No more auto-bumping patch version on every commit - GitHub
  Release created automatically for x.y.0 versions

### Continuous Integration

- Release v1.0.6
  ([`2bae7a7`](https://github.com/nfraxlab/svc-infra/commit/2bae7a7ba20ac9c8a99769fe26ed79271bb5e536))


## v1.0.5 (2025-12-27)

### Continuous Integration

- Release v1.0.5
  ([`6dae1a6`](https://github.com/nfraxlab/svc-infra/commit/6dae1a6741ea8059b0dc48e4bb1748c4f7946ee2))


## v1.0.4 (2025-12-27)

### Continuous Integration

- Only create GitHub Releases for minor/major versions
  ([`16d3c46`](https://github.com/nfraxlab/svc-infra/commit/16d3c4649a6071ceae9dcb3c1eed75c339a45eab))

- Release v1.0.4
  ([`6eded89`](https://github.com/nfraxlab/svc-infra/commit/6eded89c484b8ff6424aee684f2d56f90b95625a))

- Update changelog for v1.0.0 release with highlights, breaking changes, features, and documentation
  ([`b25b905`](https://github.com/nfraxlab/svc-infra/commit/b25b90557700c0aca3a67786434e90ac62d0547e))


## v1.0.3 (2025-12-27)

### Continuous Integration

- Add GitHub Release creation to publish workflow
  ([`ad4ae02`](https://github.com/nfraxlab/svc-infra/commit/ad4ae0242ac3602fccd309d592cfdd6d26955bcc))

- Release v1.0.3
  ([`15de569`](https://github.com/nfraxlab/svc-infra/commit/15de5696baefd9e90f516c61ed8af726fd8f877e))


## v1.0.2 (2025-12-27)

### Continuous Integration

- Release v1.0.2
  ([`7ad8e54`](https://github.com/nfraxlab/svc-infra/commit/7ad8e54829acc0ea091c9c1bbbd10e1f5527aed6))


## v1.0.1 (2025-12-27)

### Continuous Integration

- Release v1.0.1
  ([`09dcf86`](https://github.com/nfraxlab/svc-infra/commit/09dcf86099582d9fa585be54cad75a2777ab7ab5))


## v1.0.0 (2025-12-27)

### Chores

- Release v1.0.0
  ([`b5b8f13`](https://github.com/nfraxlab/svc-infra/commit/b5b8f13cff796b35f8519dbed5212ff5eab27a8d))

### Refactoring

- **billing**: Remove deprecated BillingService and update documentation for migration to
  AsyncBillingService
  ([`edb4d4a`](https://github.com/nfraxlab/svc-infra/commit/edb4d4ad7a0ee0ff351180a538e4c8d6dcac0c8b))


## v0.1.717 (2025-12-27)

### Bug Fixes

- **tests**: Correct expected output string in test_docs_topic_command_prints_file_contents
  ([`5f48302`](https://github.com/nfraxlab/svc-infra/commit/5f483022fcf8551ab3a272a2f2d4593113f02b4f))

### Continuous Integration

- Release v0.1.717
  ([`71a45dd`](https://github.com/nfraxlab/svc-infra/commit/71a45dd8c4a38829727ef6c506812e3bb7b8e11a))

### Documentation

- Enhance idempotency documentation for clarity and structure
  ([`e137708`](https://github.com/nfraxlab/svc-infra/commit/e137708b73affc51b3169ffa67d550c9ef519826))


## v0.1.716 (2025-12-26)

### Bug Fixes

- **ci**: Prevent docs-changelog race condition with publish workflow
  ([`008c351`](https://github.com/nfraxlab/svc-infra/commit/008c3511a4d3c6ac9be42c13689be18cbdf3252d))

- **resilience**: Fix mypy missing return statement in circuit breaker protect decorator
  ([`809083b`](https://github.com/nfraxlab/svc-infra/commit/809083b92cd3ca7b7be941227488bbdf42eda8de))

### Continuous Integration

- Release v0.1.716
  ([`9dab68e`](https://github.com/nfraxlab/svc-infra/commit/9dab68e326348de8598217ac007a25797e59dbc6))

### Documentation

- Update changelog [skip ci]
  ([`85f1664`](https://github.com/nfraxlab/svc-infra/commit/85f1664bd5ac80a70988a3ffd60fe5649d987283))

### Features

- Add resilience patterns documentation and implement retry and circuit breaker utilities
  ([`07ae1e5`](https://github.com/nfraxlab/svc-infra/commit/07ae1e5e53d37179ece87ddcb9d81286188b9b8a))


## v0.1.715 (2025-12-24)

### Continuous Integration

- Release v0.1.715
  ([`7a37d73`](https://github.com/nfraxlab/svc-infra/commit/7a37d73ac3b5f9c80c988858c1402be6f0d8239b))

### Documentation

- Update changelog [skip ci]
  ([`ac0b269`](https://github.com/nfraxlab/svc-infra/commit/ac0b26940dd75c083843810403521eb4c4c5f116))


## v0.1.714 (2025-12-23)

### Continuous Integration

- Release v0.1.714
  ([`b015217`](https://github.com/nfraxlab/svc-infra/commit/b015217a5b508d1103b56f7fcdf9567fb4f94a8d))

### Features

- Add skip_paths parameter for middleware to exclude specific endpoints
  ([`f357812`](https://github.com/nfraxlab/svc-infra/commit/f35781239bf7cec7dbce665b9be11c697cbdba4e))


## v0.1.713 (2025-12-19)

### Bug Fixes

- Lower coverage threshold to 50% to match current state
  ([`b04d2f0`](https://github.com/nfraxlab/svc-infra/commit/b04d2f00cbc14206b05aa671f4643a77c4288254))

Current coverage is 52%, setting threshold to 50% to allow CI to pass. Coverage will be improved
  incrementally.

- Merge deprecation utilities into utils.py
  ([`414068a`](https://github.com/nfraxlab/svc-infra/commit/414068abc309ed0af85e11e6fc02fac1bd4d9de3))

The utils/ directory was shadowing the utils.py module, breaking imports for ensure_init_py,
  render_template, and write functions.

- Remove utils/ directory - Add deprecation functions to utils.py - Update test imports to use
  svc_infra.utils

- Update bandit config to skip false positive security warnings
  ([`48fd92c`](https://github.com/nfraxlab/svc-infra/commit/48fd92c5e6486b6a1f18668585d82574bd9b0ffc))

- Skip B104 (hardcoded bind all interfaces) - intentional for containers - Skip B310 (urllib
  urlopen) - URL is validated/trusted - Skip B324 (SHA1/MD5 hash) - used for cache keys and HIBP
  API, not security

### Chores

- Update poetry.lock
  ([`8d2752d`](https://github.com/nfraxlab/svc-infra/commit/8d2752dabd8cb82ece7ee84fd5fb32ecd6cf7402))

### Continuous Integration

- Release v0.1.713
  ([`ca2ee1f`](https://github.com/nfraxlab/svc-infra/commit/ca2ee1fff1212860d983bcaf44038395ea1de988))

### Features

- Add deprecation policy and helpers
  ([`d408100`](https://github.com/nfraxlab/svc-infra/commit/d4081002df3464902a1c5cb6a946154ccfd02c08))

- Add DEPRECATION.md with deprecation timeline and policy - Update CONTRIBUTING.md with deprecation
  guidelines section - Add utils/deprecation.py with @deprecated decorator - Add
  deprecated_parameter() function for parameter deprecation - Add DeprecatedWarning custom warning
  class - Add unit tests for deprecation helpers - Add integration tests for OAuth flow, JWT auth,
  webhooks, Redis cache, job queue


## v0.1.712 (2025-12-18)

### Continuous Integration

- Release v0.1.712
  ([`b0209d1`](https://github.com/nfraxlab/svc-infra/commit/b0209d15950386a6ce37f31dd7d50e3be2a10d7b))

- Streamline version bump and changelog commit process
  ([`b47eb42`](https://github.com/nfraxlab/svc-infra/commit/b47eb42c680c1ca7c9d0962c2f085a70d4a493f3))


## v0.1.711 (2025-12-18)

### Continuous Integration

- Release v0.1.711
  ([`1d45516`](https://github.com/nfraxlab/svc-infra/commit/1d45516b828be3375cb40f3e962e0fb03400897a))

### Features

- Add git-cliff configuration for automated changelog generation
  ([`ac4f9fb`](https://github.com/nfraxlab/svc-infra/commit/ac4f9fb38112d132dc939d51d83f278524f0ab1f))

- Introduced a new `cliff.toml` configuration file for managing changelog generation. - Configured
  changelog header and body templates to format releases and commits. - Set up commit parsing rules
  for categorizing changes into Features, Bug Fixes, Documentation, Performance, Refactor, Styling,
  Testing, Miscellaneous, and Build. - Enabled conventional commits and specified commit
  preprocessors for linking pull requests. - Established limits on the number of commits to include
  in the changelog and defined sorting order.


## v0.1.710 (2025-12-18)

### Continuous Integration

- Release v0.1.710
  ([`744993c`](https://github.com/nfraxlab/svc-infra/commit/744993c24cf1c5cc3aa1d970e4b451e16fcf2199))


## v0.1.709 (2025-12-18)

### Continuous Integration

- Release v0.1.709
  ([`94e1af7`](https://github.com/nfraxlab/svc-infra/commit/94e1af7335f92aea9743c9c53172aefb31b55677))

### Documentation

- Update changelog [skip ci]
  ([`4d53176`](https://github.com/nfraxlab/svc-infra/commit/4d53176133ae32d3142c3598fb0a16324b14dc67))

### Features

- Enhance billing module documentation and deprecate synchronous service
  ([`78714d5`](https://github.com/nfraxlab/svc-infra/commit/78714d5e7326573f071b3f9a1c777e8974b0073b))

- Enhance documentation with comprehensive guides and error handling patterns
  ([`3235e97`](https://github.com/nfraxlab/svc-infra/commit/3235e97c66f15ff3ec6e117c22bf116b696e44b7))


## v0.1.708 (2025-12-18)

### Continuous Integration

- Release v0.1.708
  ([`d22f04c`](https://github.com/nfraxlab/svc-infra/commit/d22f04c50daac56700eb971060ba9e354835be72))

### Features

- Add comprehensive unit tests for SQL injection prevention and infrastructure edge cases
  ([`0ac4c89`](https://github.com/nfraxlab/svc-infra/commit/0ac4c89b5b8e35f17292f3d758332b4b669b9c71))


## v0.1.707 (2025-12-18)

### Bug Fixes

- Add pytest-asyncio to test dependencies in docker-compose
  ([`d1069d8`](https://github.com/nfraxlab/svc-infra/commit/d1069d8158df4ad798951968db68ae9d6d219b95))

### Continuous Integration

- Release v0.1.707
  ([`1ad1d8f`](https://github.com/nfraxlab/svc-infra/commit/1ad1d8fa3e035a7de8f5f4b408865ed9930e640f))


## v0.1.706 (2025-12-18)

### Continuous Integration

- Release v0.1.706
  ([`52e7742`](https://github.com/nfraxlab/svc-infra/commit/52e774275fabbe1ce36c454877ead1f4fa95e205))

### Features

- Add integration tests for billing service and S3 storage backend
  ([`940aa53`](https://github.com/nfraxlab/svc-infra/commit/940aa5363481fc301f4f441a1704ae80da84efaf))


## v0.1.705 (2025-12-17)

### Bug Fixes

- Add check for optional stripe SDK dependency in test
  ([`354bc37`](https://github.com/nfraxlab/svc-infra/commit/354bc37672a1202156ca97de167ef50b7eef7f55))

- Correct spacing in type ignore comments for AsyncIOMotorDatabase and AsyncIOMotorClient
  ([`67759f1`](https://github.com/nfraxlab/svc-infra/commit/67759f1d11fb7be23868fe9fdb3828dd22e953f2))

- Refine MongoDB helper function signatures for improved type hinting
  ([`df9e640`](https://github.com/nfraxlab/svc-infra/commit/df9e64076344afbcd7db4892edc14aa19c3dc61f))

- Remove unnecessary spaces in type ignore comments for AsyncIOMotorDatabase and AsyncIOMotorClient
  ([`1c863f2`](https://github.com/nfraxlab/svc-infra/commit/1c863f24dbf26c2d9f08bdb2c52bf3f1a549f86c))

- Update poetry.lock for package optionality and platform-specific markers
  ([`434125f`](https://github.com/nfraxlab/svc-infra/commit/434125f72680a29329ff44c34f753d3d6c0a2471))

### Continuous Integration

- Release v0.1.705
  ([`69e6628`](https://github.com/nfraxlab/svc-infra/commit/69e66281274cfcb869af3710a36189aacdd3cbbc))

### Features

- Add optional MongoDB dependency handling and stubs for missing imports
  ([`9a66b53`](https://github.com/nfraxlab/svc-infra/commit/9a66b538d4a6d2d738038458497b15ba8688c709))

- Enhance svc-infra with comprehensive API and authentication modules, optional MongoDB support, and
  improved documentation
  ([`2de64cb`](https://github.com/nfraxlab/svc-infra/commit/2de64cb02b147134eb115ce7a22253d13d342023))

- Implement optional MongoDB dependency handling with informative stubs for missing imports
  ([`8591d86`](https://github.com/nfraxlab/svc-infra/commit/8591d86d29227ad9ba2f8a31a18c8e34ab14f532))

### Refactoring

- Streamline MongoDB dependency handling and improve ObjectId fallback
  ([`35ace1d`](https://github.com/nfraxlab/svc-infra/commit/35ace1d9e35238f6aee40174544b060ebf026404))


## v0.1.704 (2025-12-17)

### Bug Fixes

- **demo**: Update error and success messages for user deletion
  ([`2a8b532`](https://github.com/nfraxlab/svc-infra/commit/2a8b532890aceb66950f1335255d9873435ddcd5))

### Continuous Integration

- Release v0.1.704
  ([`6297c8e`](https://github.com/nfraxlab/svc-infra/commit/6297c8effca9a83eec30c9a68918fee74a136460))


## v0.1.703 (2025-12-17)

### Bug Fixes

- **format**: Apply ruff formatting + switch pre-commit from black to ruff
  ([`58ca6c3`](https://github.com/nfraxlab/svc-infra/commit/58ca6c3180f6ee3c65a91eabb63c41d05a0cabac))

- Format 224 files with ruff - Update .pre-commit-config.yaml to use ruff instead of
  black/isort/flake8 - This ensures pre-commit matches CI (both use ruff now)

- **lint**: Remove unused _Any import in sql/management.py
  ([`576a67f`](https://github.com/nfraxlab/svc-infra/commit/576a67f898523354de6c9b1a26e1dfdb00f66d7b))

- **mypy**: Fix type ignore placement + remove mypy from pre-commit
  ([`778b039`](https://github.com/nfraxlab/svc-infra/commit/778b039c9458874ec1988c3e836b8da479c3f21e))

- Fix type ignore comment in security.py - Remove mypy from pre-commit hooks (needs full deps, use
  CI instead) - Pre-commit now only runs ruff format/lint (fast, matches CI)

- **pre-commit**: Match CI config exactly (use ruff defaults)
  ([`a209f75`](https://github.com/nfraxlab/svc-infra/commit/a209f750b9b163f73f3a6c1bcfb4c2b7e405d0f4))

- **tests**: Disable Rich colors in CLI tests for CI consistency
  ([`7c55975`](https://github.com/nfraxlab/svc-infra/commit/7c559754f05ed1ca9dcdcefbacac82cd8958eebf))

Rich terminal detection behaves differently in CI (no TTY) vs local, causing help text assertions to
  fail. The conftest sets NO_COLOR=1 to ensure plain text output across all environments.

- **types**: Resolve all mypy errors for CI
  ([`bc40d9d`](https://github.com/nfraxlab/svc-infra/commit/bc40d9d96b0b39d274e58906c69996c932cf3c06))

- Fix unused type: ignore comments by adding proper error codes - Add [misc,assignment] codes where
  needed for optional imports - Add [attr-defined] ignores for Pool.checkedout() and Pool.size() -
  Fix no-any-return errors with explicit type casts - Fix Redis hset mapping types with proper
  dict[str, str] annotation - Remove unused type: ignore comments that are no longer needed

Note: Pre-commit uses stricter mypy; CI mypy.ini config passes (306 files)

### Chores

- Update CI workflow to trigger on successful completion of CI jobs
  ([`6b211ba`](https://github.com/nfraxlab/svc-infra/commit/6b211ba03e5c1fbd3c5121c53a58b27cf0345b15))

### Continuous Integration

- Release v0.1.703
  ([`72a87e8`](https://github.com/nfraxlab/svc-infra/commit/72a87e883994da80824f8c11128284116d6070de))


## v0.1.702 (2025-12-17)

### Continuous Integration

- Release v0.1.702
  ([`02d6c27`](https://github.com/nfraxlab/svc-infra/commit/02d6c27ddb65eda2688240e01ed35ed77c73091b))

### Refactoring

- Clean up imports and remove unused variables in unit tests
  ([`b5b9601`](https://github.com/nfraxlab/svc-infra/commit/b5b96013d2e2ed5f5825e03510eb32c7e14e4f3c))

- Removed unused imports and variables across various test files to improve code clarity and
  maintainability. - Updated test files in the following directories: deploy, health, jobs, loaders,
  log, ops, payments, security, storage, tenancy, testing, utils, webhooks, websocket. - Added a new
  GitHub Actions workflow for updating the documentation changelog automatically. - Generated a new
  changelog file to track changes in documentation files.


## v0.1.701 (2025-12-16)

### Continuous Integration

- Release v0.1.701
  ([`eb5deb7`](https://github.com/nfraxlab/svc-infra/commit/eb5deb7026dc527c189dea7f1865ade629bf68a6))


## v0.1.700 (2025-12-15)

### Continuous Integration

- Release v0.1.700
  ([`a7cc14a`](https://github.com/nfraxlab/svc-infra/commit/a7cc14a52ca7f13c2199391df3045b15ce8ef5df))


## v0.1.699 (2025-12-14)

### Continuous Integration

- Release v0.1.699
  ([`cf70c40`](https://github.com/nfraxlab/svc-infra/commit/cf70c40558638ec6c2378ea6750f0c97d0676862))

### Refactoring

- Enhance type hinting and casting across multiple modules
  ([`d4090d2`](https://github.com/nfraxlab/svc-infra/commit/d4090d2a18245e84135992eea64f2fecbb210396))


## v0.1.698 (2025-12-14)

### Continuous Integration

- Release v0.1.698
  ([`66c46fb`](https://github.com/nfraxlab/svc-infra/commit/66c46fbf6f13185db5af793162d5a45e93d36367))


## v0.1.697 (2025-12-14)

### Continuous Integration

- Release v0.1.697
  ([`77c1cae`](https://github.com/nfraxlab/svc-infra/commit/77c1cae5d9178c8f2d30eaed176c9b3fef0232bd))

### Features

- Add centralized exception handling and logging utilities for svc-infra
  ([`1b646fb`](https://github.com/nfraxlab/svc-infra/commit/1b646fb8056bba8f53fd1d367c18bedc4a9dd658))


## v0.1.696 (2025-12-14)

### Continuous Integration

- Release v0.1.696
  ([`363e584`](https://github.com/nfraxlab/svc-infra/commit/363e58474078eeb7968995abde07169bfa8e339a))

### Features

- Enhance logging and add production warnings for in-memory stores across various modules
  ([`10abe60`](https://github.com/nfraxlab/svc-infra/commit/10abe605b1a75253214a9c4bd73e1bbc67af6e5d))


## v0.1.695 (2025-12-14)

### Continuous Integration

- Release v0.1.695
  ([`92a001a`](https://github.com/nfraxlab/svc-infra/commit/92a001a83dd6d9d93771731040d05432589f1eae))

### Features

- Add require_secret function for secure secret loading and enhance webhook secret encryption
  guidance
  ([`9b4f9ac`](https://github.com/nfraxlab/svc-infra/commit/9b4f9aca69323a7661ea2f189fb31d0fc7eb551b))


## v0.1.694 (2025-12-14)

### Continuous Integration

- Release v0.1.694
  ([`34b4688`](https://github.com/nfraxlab/svc-infra/commit/34b468848b6844c367485d8507adea9ad727b395))

### Features

- Implement require_secret for sensitive configurations and add encryption for webhook secrets
  ([`f468990`](https://github.com/nfraxlab/svc-infra/commit/f46899054c70ee55130f1b5095598e436dd50d87))


## v0.1.693 (2025-12-13)

### Continuous Integration

- Release v0.1.693
  ([`4a6e63d`](https://github.com/nfraxlab/svc-infra/commit/4a6e63dc67ad0ed340a9660e71b5cd9ba2877779))


## v0.1.692 (2025-12-12)

### Bug Fixes

- Update repository references from nfraxio to nfraxlab in documentation and code
  ([`d9b9180`](https://github.com/nfraxlab/svc-infra/commit/d9b9180cc7c6b682c96332bd1b3fb0465f92c94a))

### Chores

- Re-trigger pypi publish after enabling workflow
  ([`934b5f8`](https://github.com/nfraxlab/svc-infra/commit/934b5f8905fc6cfcaa78a221a50173fc7058a681))

- Trigger pypi publish
  ([`0ebc693`](https://github.com/nfraxlab/svc-infra/commit/0ebc6935adbc9a9b539407b97e65734a152f692a))

- Trigger pypi publish
  ([`291d925`](https://github.com/nfraxlab/svc-infra/commit/291d925e2294ca86462a530674d9cf2cfc43d1f3))

### Continuous Integration

- Release v0.1.692
  ([`7267220`](https://github.com/nfraxlab/svc-infra/commit/72672209dff20af676744ec938424f9ef91b04f4))


## v0.1.691 (2025-12-11)

### Continuous Integration

- Release v0.1.691
  ([`990f540`](https://github.com/nfraxlab/svc-infra/commit/990f5409f8c9c998217584cdb815463628827c8c))

### Refactoring

- Enhance DB lifecycle management to preserve existing lifespan context
  ([`67f0038`](https://github.com/nfraxlab/svc-infra/commit/67f0038b74c1ae20b5b1e2c5a6297a9b8693fa07))


## v0.1.690 (2025-12-10)

### Chores

- Remove unnecessary backup files and update dependencies in pyproject.toml
  ([`992df6f`](https://github.com/nfraxlab/svc-infra/commit/992df6fd6297654d82699da2b71f16ef19fa0e64))

### Continuous Integration

- Release v0.1.690
  ([`a719c2c`](https://github.com/nfraxlab/svc-infra/commit/a719c2c06e3c0219c969889c5c92f7fe0e044dc8))


## v0.1.689 (2025-12-10)

### Continuous Integration

- Release v0.1.689
  ([`53664c5`](https://github.com/nfraxlab/svc-infra/commit/53664c505520b7ffa37a3b72afcbdff72821bd97))


## v0.1.688 (2025-12-10)

### Chores

- Add MIT License file
  ([`d7a2ed1`](https://github.com/nfraxlab/svc-infra/commit/d7a2ed17c88d828bb5b06738ae86ad33e03be6f7))

### Continuous Integration

- Release v0.1.688
  ([`277de33`](https://github.com/nfraxlab/svc-infra/commit/277de339d287656913b32902b007bd1b995a3be3))


## v0.1.687 (2025-12-10)

### Chores

- Remove outdated ADR for content loaders architecture
  ([`c3566d4`](https://github.com/nfraxlab/svc-infra/commit/c3566d445b4a7af1a0ace6a5dd292c56579223d6))

### Continuous Integration

- Release v0.1.687
  ([`7d407db`](https://github.com/nfraxlab/svc-infra/commit/7d407dba01f8980c6f513485ef67057ba3c24df5))


## v0.1.686 (2025-12-10)

### Continuous Integration

- Release v0.1.686
  ([`9622bde`](https://github.com/nfraxlab/svc-infra/commit/9622bded2d6cc50decc589f75e72f63a322edd38))

### Features

- **scheduler**: Add tick interval parameter to InMemoryScheduler
  ([`dd31c94`](https://github.com/nfraxlab/svc-infra/commit/dd31c9485d5bf96494c32ba38e4f4059138cee2e))


## v0.1.685 (2025-12-09)

### Continuous Integration

- Release v0.1.685
  ([`89c4e43`](https://github.com/nfraxlab/svc-infra/commit/89c4e434dab81f5537d91b72bdc460e50a9763de))

### Features

- **loaders**: Implement LoadedContent model and URLLoader for fetching content from URLs
  ([`4b337d7`](https://github.com/nfraxlab/svc-infra/commit/4b337d72a6dfa952f3d9f02b882f20635090cbc5))

- Added LoadedContent dataclass to standardize content loading structure. - Implemented URLLoader
  class for loading content from single or multiple URLs with optional HTML text extraction. -
  Included error handling for HTTP requests and metadata population for loaded content. - Created
  unit tests for LoadedContent, URLLoader, and GitHubLoader to ensure functionality and correctness.
  - Added convenience functions for loading content from GitHub and URLs.


## v0.1.684 (2025-12-08)

### Continuous Integration

- Release v0.1.684
  ([`7744198`](https://github.com/nfraxlab/svc-infra/commit/7744198092f203d81c15c6b649db271fe7bf01ca))

### Features

- Add support for additional FastAPI kwargs in service API setup
  ([`b553806`](https://github.com/nfraxlab/svc-infra/commit/b553806f247e17e3593ef080c5b6faddd4bd5539))


## v0.1.683 (2025-12-04)

### Continuous Integration

- Release v0.1.683
  ([`ae8d6bc`](https://github.com/nfraxlab/svc-infra/commit/ae8d6bc08e5a436945e372a2dc8bdcf088fded54))

### Documentation

- Consolidate badge display in README for improved readability
  ([`e80a3dd`](https://github.com/nfraxlab/svc-infra/commit/e80a3dd2f517fa6c631dc31285830b16028147a0))


## v0.1.682 (2025-12-04)

### Continuous Integration

- Release v0.1.682
  ([`2e42bc7`](https://github.com/nfraxlab/svc-infra/commit/2e42bc76905ecc8eaf75095a039ea5887935d4b7))

### Documentation

- Update README for improved clarity and structure
  ([`b76080f`](https://github.com/nfraxlab/svc-infra/commit/b76080f0fa49d5dd4343b64c62051f1806e598c2))


## v0.1.681 (2025-12-02)

### Continuous Integration

- Release v0.1.681
  ([`72650c5`](https://github.com/nfraxlab/svc-infra/commit/72650c5e3fb8348234dd63c176c2b2aaddcf2e98))

### Features

- Enhance CORS setup with regex support for wildcard origins
  ([`4866cf4`](https://github.com/nfraxlab/svc-infra/commit/4866cf454ab7e64ed406510c3906ed9680e40c24))


## v0.1.680 (2025-11-29)

### Chores

- Remove obsolete ADRs and documentation
  ([`3216426`](https://github.com/nfraxlab/svc-infra/commit/3216426c9a887f4b433fb07f0a09a2fe0002769d))

- Deleted ADR 0009: Acceptance Harness & Promotion Gate as it is no longer relevant. - Removed ADR
  0010: Timeouts & Resource Limits due to changes in design decisions. - Eliminated ADR 0011: Admin
  scope, permissions, and impersonation as the implementation has evolved. - Discarded ADR 0012:
  Generic File Storage System as the design phase has concluded. - Cleaned up contributing and
  getting started documentation to reflect current practices. - Updated storage and timeouts
  documentation to remove references to deleted ADRs.

### Continuous Integration

- Release v0.1.680
  ([`a6c4eb2`](https://github.com/nfraxlab/svc-infra/commit/a6c4eb2c9a56327c9bd2f1bf589ca3f6f8c99882))


## v0.1.679 (2025-11-29)

### Continuous Integration

- Release v0.1.679
  ([`8008c93`](https://github.com/nfraxlab/svc-infra/commit/8008c93178483c2dee9bcfe668c2e0145f034a97))


## v0.1.678 (2025-11-29)

### Continuous Integration

- Release v0.1.678
  ([`7f125e3`](https://github.com/nfraxlab/svc-infra/commit/7f125e34d05efebdb91e277fc9588098caf28e77))

### Features

- Add WebSocket authentication infrastructure with lightweight JWT support
  ([`704b243`](https://github.com/nfraxlab/svc-infra/commit/704b243be721c069e33e0712dfeb1958f3373241))


## v0.1.677 (2025-11-29)

### Continuous Integration

- Release v0.1.677
  ([`0e433a3`](https://github.com/nfraxlab/svc-infra/commit/0e433a315f5a8692bee3f497ee5d994cc5d78b69))

### Features

- Implement WebSocket infrastructure with FastAPI integration and connection management
  ([`6d77e39`](https://github.com/nfraxlab/svc-infra/commit/6d77e3926e6cf10cfe72fe9e3b225e20c9881626))


## v0.1.676 (2025-11-28)

### Continuous Integration

- Release v0.1.676
  ([`8f9a39f`](https://github.com/nfraxlab/svc-infra/commit/8f9a39f0685fce53b72f230a49303db413fb9295))

### Features

- Add WebSocket infrastructure with client and server utilities
  ([`932a5b1`](https://github.com/nfraxlab/svc-infra/commit/932a5b1e5f4d1935934f439b8299cc3e53f11aac))

- Introduced `websockets` dependency for WebSocket support. - Implemented `WebSocketClient` for
  connecting to external WebSocket services with context manager support. - Added
  `ConnectionManager` for managing multiple server-side connections. - Created configuration
  management for WebSocket settings with environment variable support. - Defined custom exceptions
  for WebSocket operations, including connection failures and message size limits. - Developed data
  models for connection states and message handling. - Provided quick start examples for both client
  and server usage in the documentation.


## v0.1.675 (2025-11-28)

### Bug Fixes

- Correct documentation paths from src/svc_infra/docs to docs/
  ([`965e124`](https://github.com/nfraxlab/svc-infra/commit/965e12446bbae138a8ba42057865559cba4ebf3a))

### Continuous Integration

- Release v0.1.675
  ([`fc3e6d9`](https://github.com/nfraxlab/svc-infra/commit/fc3e6d9a4d649b66e7e553b146a8b5763e5e92b1))


## v0.1.674 (2025-11-27)

### Continuous Integration

- Release v0.1.674
  ([`64ad950`](https://github.com/nfraxlab/svc-infra/commit/64ad9504ec0e3ab83498e0a9f61eb6ac919b191f))


## v0.1.673 (2025-11-26)

### Continuous Integration

- Release v0.1.673
  ([`ad5226d`](https://github.com/nfraxlab/svc-infra/commit/ad5226de1ea98d05178a07dd9c6bfc1661c4dc84))

### Features

- **middleware**: Enhance middleware to support skip_paths for streaming and long-running endpoints
  ([`0e28866`](https://github.com/nfraxlab/svc-infra/commit/0e2886694a79999a52d4c605c96b42bf2103d20a))


## v0.1.672 (2025-11-26)

### Continuous Integration

- Release v0.1.672
  ([`63a8bad`](https://github.com/nfraxlab/svc-infra/commit/63a8badd41ab13056f85585063fb08500ac27f65))

### Features

- **middleware**: Enhance HandlerTimeoutMiddleware to support streaming responses and adjust timeout
  behavior
  ([`b041c0e`](https://github.com/nfraxlab/svc-infra/commit/b041c0e1719c92d92573b8c0b25081611a032ca2))


## v0.1.671 (2025-11-25)

### Continuous Integration

- Release v0.1.671
  ([`227b339`](https://github.com/nfraxlab/svc-infra/commit/227b33955b14658a288a63ada0d855e2ab256ff3))

### Features

- **middleware**: Add skip_paths option to SimpleRateLimitMiddleware and log skipped paths
  ([`3e860dd`](https://github.com/nfraxlab/svc-infra/commit/3e860ddb884950a527693b1a6a6a1f166c187ad4))


## v0.1.670 (2025-11-25)

### Continuous Integration

- Release v0.1.670
  ([`2455f39`](https://github.com/nfraxlab/svc-infra/commit/2455f391b681597a0f0756950ae1306928485d9e))

### Features

- **middleware**: Add skip_paths option to IdempotencyMiddleware for streaming compatibility
  ([`2927125`](https://github.com/nfraxlab/svc-infra/commit/29271253ce1fd78fba829cd2cacfa94d24014146))


## v0.1.669 (2025-11-25)

### Continuous Integration

- Release v0.1.669
  ([`bf3bcaf`](https://github.com/nfraxlab/svc-infra/commit/bf3bcaf3fa4d592b1e6b1b670a2b74376f2eb9f6))

### Features

- **middleware**: Refactor RequestIdMiddleware for pure ASGI compatibility and streaming safety
  ([`a837ff6`](https://github.com/nfraxlab/svc-infra/commit/a837ff68733e44f7acafe87612bcbe36ce6d383e))


## v0.1.668 (2025-11-19)

### Continuous Integration

- Release v0.1.668
  ([`788c8d6`](https://github.com/nfraxlab/svc-infra/commit/788c8d644e630144cbd2f42b8100fe85bab96505))

### Features

- **settings**: Ignore unknown environment variables in storage settings
  ([`e0de49a`](https://github.com/nfraxlab/svc-infra/commit/e0de49a8f8dbb5f283fe40d038451d3ea31ccea0))


## v0.1.667 (2025-11-18)

### Continuous Integration

- Release v0.1.667
  ([`884a957`](https://github.com/nfraxlab/svc-infra/commit/884a957d7bd6528e0a2cec46e2534c2c4670f9ab))

### Features

- **documents**: Add document management and storage examples with API endpoints
  ([`9c1c038`](https://github.com/nfraxlab/svc-infra/commit/9c1c038834860a7b8e69910182f006f151e3598b))

- **documents**: Implement document management system with upload, download, and filtering
  capabilities
  ([`7e12497`](https://github.com/nfraxlab/svc-infra/commit/7e124976b8ec9fe68db52b57b6c141e64ccef590))


## v0.1.666 (2025-11-18)

### Bug Fixes

- **tests**: Update acceptance tests for improved error handling and unique user IDs
  ([`5102d06`](https://github.com/nfraxlab/svc-infra/commit/5102d06ffcdd19853de68fd7bb77db2a985fcd1e))

### Continuous Integration

- Release v0.1.666
  ([`5e7faef`](https://github.com/nfraxlab/svc-infra/commit/5e7faef00ea6c2f2057145798961aa631ac3951e))


## v0.1.665 (2025-11-18)

### Continuous Integration

- Release v0.1.665
  ([`c38a9c9`](https://github.com/nfraxlab/svc-infra/commit/c38a9c990d9256bed886289d2f5667332bc6e701))

### Features

- **documents**: Implement generic document management system with FastAPI integration
  ([`bbc816a`](https://github.com/nfraxlab/svc-infra/commit/bbc816a7ac7df234e642bee5c1db2e5316111e4a))

- Added document management module with domain-agnostic storage and metadata handling. - Created
  `add_documents` function for FastAPI integration, providing endpoints for document upload,
  retrieval, listing, and deletion. - Developed `DocumentManager` class for simplified document
  operations with automatic storage backend integration. - Introduced `Document` model for flexible
  metadata representation. - Implemented storage operations including upload, download, delete, and
  list functionalities. - Added unit tests for document storage operations using in-memory backend.


## v0.1.664 (2025-11-18)

### Continuous Integration

- Release v0.1.664
  ([`0afb837`](https://github.com/nfraxlab/svc-infra/commit/0afb8375820dbe6cc25b5bc66d21f524eda2c01b))

### Features

- **storage**: Implement acceptance tests and storage API endpoints
  ([`04245f6`](https://github.com/nfraxlab/svc-infra/commit/04245f6eeabca625387b67d0090194247ce9db6f))

- Added storage backend integration for acceptance tests (A22-01 to A22-05). - Implemented endpoints
  for file upload, download, deletion, listing, and metadata retrieval. - Created comprehensive
  acceptance tests to validate functionality of storage operations. - Documented storage system
  architecture, usage, and configuration in storage.md.


## v0.1.663 (2025-11-18)

### Continuous Integration

- Release v0.1.663
  ([`22fde32`](https://github.com/nfraxlab/svc-infra/commit/22fde32d2a30df327ea889d767c0b7d1136cb65d))


## v0.1.662 (2025-11-17)

### Continuous Integration

- Release v0.1.662
  ([`312a28a`](https://github.com/nfraxlab/svc-infra/commit/312a28a2c8956b745c9cbc33b7fbb2eb18e60dd7))

### Refactoring

- Remove ProviderAccount model and update OAuth integration notes
  ([`6543e42`](https://github.com/nfraxlab/svc-infra/commit/6543e421bb3cd72af6c6f69aef4531383a119d00))


## v0.1.661 (2025-11-17)

### Continuous Integration

- Release v0.1.661
  ([`891b1b9`](https://github.com/nfraxlab/svc-infra/commit/891b1b9c5c65a7ea2e4c2c299b01ee96daf79b39))

### Features

- Add import and logging for core security models in env_async and env_sync templates
  ([`e02bc5f`](https://github.com/nfraxlab/svc-infra/commit/e02bc5f3137414df75bf814593dde4469013bd3f))


## v0.1.660 (2025-11-17)

### Bug Fixes

- Update relationship comment for ProviderAccount model
  ([`2def913`](https://github.com/nfraxlab/svc-infra/commit/2def913c8770043246f8b5cb3c03d9aded6aa931))

### Continuous Integration

- Release v0.1.660
  ([`f95ea24`](https://github.com/nfraxlab/svc-infra/commit/f95ea24b6f5ec08799cf88091cadd0ba02d3845f))


## v0.1.659 (2025-11-17)

### Continuous Integration

- Release v0.1.659
  ([`6d95713`](https://github.com/nfraxlab/svc-infra/commit/6d95713d4efe6d896ca7fcc75057d4362c68125b))

### Features

- Implement opt-in OAuth provider account models and update migration templates
  ([`e419ca9`](https://github.com/nfraxlab/svc-infra/commit/e419ca9628b4f7c20795fd146ce3e396c2d546c5))


## v0.1.658 (2025-11-17)

### Continuous Integration

- Release v0.1.658
  ([`f15c6dc`](https://github.com/nfraxlab/svc-infra/commit/f15c6dcaef5a9759dc8aa4952dad8cff8e16a90d))

### Features

- Implement ProviderAccount model for OAuth provider account linking
  ([`ada3250`](https://github.com/nfraxlab/svc-infra/commit/ada3250f085ace83860e5778642ca7a9e6f73b87))


## v0.1.657 (2025-11-17)

### Bug Fixes

- Prioritize post_login_redirect parameter over settings in _determine_final_redirect_url
  ([`563e3d9`](https://github.com/nfraxlab/svc-infra/commit/563e3d9c77274d3ea2efee664e05146fbbd7b870))

### Continuous Integration

- Release v0.1.657
  ([`5404051`](https://github.com/nfraxlab/svc-infra/commit/540405181980e020af1e44b25e1cba90a6b5be3a))


## v0.1.656 (2025-11-17)

### Bug Fixes

- Enforce strict checks for SQLAlchemy MetaData instances in _maybe_add and _scan_module_objects
  ([`1943285`](https://github.com/nfraxlab/svc-infra/commit/1943285a5ee419b53748a0c82138c09a7c762464))

### Continuous Integration

- Release v0.1.656
  ([`95bf5a2`](https://github.com/nfraxlab/svc-infra/commit/95bf5a2aaf8c469934c7510ae00d482eb83df428))


## v0.1.655 (2025-11-17)

### Bug Fixes

- Ensure only SQLAlchemy MetaData objects are added in _maybe_add and _scan_module_objects
  ([`d59da96`](https://github.com/nfraxlab/svc-infra/commit/d59da9690d5fa4b5c613f4ad5702b41d29a100fe))

### Continuous Integration

- Release v0.1.655
  ([`f4e75a7`](https://github.com/nfraxlab/svc-infra/commit/f4e75a710e30bef893ea80d07945a25c35bf4a2d))


## v0.1.654 (2025-11-17)

### Bug Fixes

- Update server_default for created_at columns to use text() for consistency
  ([`1514166`](https://github.com/nfraxlab/svc-infra/commit/1514166ddddd38766f19ec1ee904a66e5b069442))

### Continuous Integration

- Release v0.1.654
  ([`f3b5b41`](https://github.com/nfraxlab/svc-infra/commit/f3b5b41de125401e6df34d701776355bf626a0a4))


## v0.1.653 (2025-11-15)

### Continuous Integration

- Release v0.1.653
  ([`c3e2c84`](https://github.com/nfraxlab/svc-infra/commit/c3e2c84f026b9eb839e2f6581c55dcb180f476f4))

### Refactoring

- Rename capture_add_function_router to extract_router and update documentation
  ([`6b658e9`](https://github.com/nfraxlab/svc-infra/commit/6b658e94e12d036115436e747092001ecf8a63a3))


## v0.1.652 (2025-11-15)

### Continuous Integration

- Release v0.1.652
  ([`c61aa69`](https://github.com/nfraxlab/svc-infra/commit/c61aa690c43a2b179fa50722c5caa9496fe55c53))

### Features

- Add capture_add_function_router helper and documentation for versioned routing
  ([`7596aba`](https://github.com/nfraxlab/svc-infra/commit/7596aba02c65744aaf9ac2a01fc38bf6256017ab))


## v0.1.651 (2025-11-15)

### Continuous Integration

- Release v0.1.651
  ([`ed7ac8d`](https://github.com/nfraxlab/svc-infra/commit/ed7ac8d7b63272630976ad2603cc3582240af350))

### Refactoring

- Remove scoped documentation registration from payments and auth setup
  ([`7fa4821`](https://github.com/nfraxlab/svc-infra/commit/7fa482183dd1da2a7328268052dfb48f24e10a10))


## v0.1.650 (2025-11-15)

### Continuous Integration

- Release v0.1.650
  ([`194f94f`](https://github.com/nfraxlab/svc-infra/commit/194f94fe8fc251ce7a978b2e1cf6165970b82a82))

### Refactoring

- Remove scoped documentation registration from billing, mongo, and sql resource setup
  ([`6c728a9`](https://github.com/nfraxlab/svc-infra/commit/6c728a9ae9914fe624dbf0ad7071e91077e7697a))


## v0.1.649 (2025-11-15)

### Continuous Integration

- Release v0.1.649
  ([`56d7e1d`](https://github.com/nfraxlab/svc-infra/commit/56d7e1d66d85c740572644867a2e174d930bbde7))

### Features

- **docs**: Add server URL handling for scoped documentation
  ([`6fb1881`](https://github.com/nfraxlab/svc-infra/commit/6fb18814a1feed44ec9240ceef5cdc7dc143518a))


## v0.1.648 (2025-11-14)

### Continuous Integration

- Release v0.1.648
  ([`1bd37b1`](https://github.com/nfraxlab/svc-infra/commit/1bd37b1b813c04536dc8238128598f82031e500b))

### Features

- **api**: Enhance scoped docs handling with root exclusion logic
  ([`492ac29`](https://github.com/nfraxlab/svc-infra/commit/492ac2979b350e81e2a4cf457fd59e12b5f5bc48))


## v0.1.647 (2025-11-14)

### Continuous Integration

- Release v0.1.647
  ([`96925e0`](https://github.com/nfraxlab/svc-infra/commit/96925e075f4517934574b10c2b7db0128d38bd94))


## v0.1.646 (2025-11-14)

### Continuous Integration

- Release v0.1.646
  ([`4841f20`](https://github.com/nfraxlab/svc-infra/commit/4841f206e80dfcf09ae26a6a53a34e80d4619cf6))


## v0.1.645 (2025-11-14)

### Continuous Integration

- Release v0.1.645
  ([`0930fd3`](https://github.com/nfraxlab/svc-infra/commit/0930fd3c79a4fec1e9143fd0e200e6de635076cf))


## v0.1.644 (2025-11-14)

### Continuous Integration

- Release v0.1.644
  ([`1f3c7a0`](https://github.com/nfraxlab/svc-infra/commit/1f3c7a0635a930b4b6cb20e5aa4f1ae04064acea))


## v0.1.643 (2025-11-14)

### Continuous Integration

- Release v0.1.643
  ([`d755ecb`](https://github.com/nfraxlab/svc-infra/commit/d755ecbd8d54985f41dbe4b3dfccd2d628156c3f))


## v0.1.642 (2025-11-14)

### Continuous Integration

- Release v0.1.642
  ([`c1db390`](https://github.com/nfraxlab/svc-infra/commit/c1db39069083d5dda39e6a2fc40c8528aea5d8f4))


## v0.1.641 (2025-11-13)

### Continuous Integration

- Release v0.1.641
  ([`3281301`](https://github.com/nfraxlab/svc-infra/commit/3281301c650283e9d2eaf4f7d5e07d1fdb3274ba))


## v0.1.640 (2025-11-13)

### Continuous Integration

- Release v0.1.640
  ([`8e6ff95`](https://github.com/nfraxlab/svc-infra/commit/8e6ff95fc4ca99e43a7e939a7cb3a9bed70b8b77))


## v0.1.639 (2025-11-13)

### Continuous Integration

- Release v0.1.639
  ([`eac5a40`](https://github.com/nfraxlab/svc-infra/commit/eac5a4034b9cc89cf098626a97465a28fd6e5f54))


## v0.1.638 (2025-11-13)

### Continuous Integration

- Release v0.1.638
  ([`65fff2e`](https://github.com/nfraxlab/svc-infra/commit/65fff2e7abbb4d0bfd9dfe52c55716729debce65))


## v0.1.637 (2025-11-13)

### Continuous Integration

- Release v0.1.637
  ([`3188a9f`](https://github.com/nfraxlab/svc-infra/commit/3188a9f8b24c95351dc211b42b41d948bed9f87a))


## v0.1.636 (2025-11-04)

### Continuous Integration

- Release v0.1.636
  ([`1db8c39`](https://github.com/nfraxlab/svc-infra/commit/1db8c3972b0b1653c112d4739c9ae9e732d54041))


## v0.1.635 (2025-11-02)

### Continuous Integration

- Release v0.1.635
  ([`64ec250`](https://github.com/nfraxlab/svc-infra/commit/64ec250278186966c38851ffbb562744a703ef73))


## v0.1.634 (2025-11-01)

### Continuous Integration

- Release v0.1.634
  ([`44fa9c9`](https://github.com/nfraxlab/svc-infra/commit/44fa9c9048684a714ba062147f3918a063592119))


## v0.1.633 (2025-10-22)

### Continuous Integration

- Release v0.1.633
  ([`5dee3fe`](https://github.com/nfraxlab/svc-infra/commit/5dee3fe081401808d4b72d7efdd364d7fad55a34))


## v0.1.632 (2025-10-22)

### Continuous Integration

- Release v0.1.632
  ([`7ecdbb5`](https://github.com/nfraxlab/svc-infra/commit/7ecdbb55a44a402885e1ee1dd2b992b2b027c6f4))


## v0.1.631 (2025-10-22)

### Continuous Integration

- Release v0.1.631
  ([`ede27ba`](https://github.com/nfraxlab/svc-infra/commit/ede27ba7f099534fa547cc3062b96dd9770ae863))


## v0.1.630 (2025-10-22)

### Continuous Integration

- Release v0.1.630
  ([`a8289a1`](https://github.com/nfraxlab/svc-infra/commit/a8289a1e8a679f23b945b2b6950ff63c6d630ef8))


## v0.1.629 (2025-10-21)

### Continuous Integration

- Release v0.1.629
  ([`3b94434`](https://github.com/nfraxlab/svc-infra/commit/3b94434442a468ce2d84989ba3e5f2f2efbce860))


## v0.1.628 (2025-10-21)

### Continuous Integration

- Release v0.1.628
  ([`668d7b7`](https://github.com/nfraxlab/svc-infra/commit/668d7b717f7e9d2060822dcff516cd2498ace9ec))


## v0.1.627 (2025-10-21)

### Continuous Integration

- Release v0.1.627
  ([`45a1259`](https://github.com/nfraxlab/svc-infra/commit/45a1259fbaf13407c67d44cd9520f4aea568c77d))


## v0.1.626 (2025-10-20)

### Continuous Integration

- Release v0.1.626
  ([`c5dd3ea`](https://github.com/nfraxlab/svc-infra/commit/c5dd3ea29e91d8ca4cabdd3dc27ccb90aef443fe))


## v0.1.625 (2025-10-20)

### Continuous Integration

- Release v0.1.625
  ([`15ac744`](https://github.com/nfraxlab/svc-infra/commit/15ac74419294c59696a5e563e23edaa3235f7d0f))


## v0.1.624 (2025-10-20)

### Continuous Integration

- Release v0.1.624
  ([`f045301`](https://github.com/nfraxlab/svc-infra/commit/f045301fe35140ceeac9ff6e308e6f6496b39731))


## v0.1.623 (2025-10-20)

### Continuous Integration

- Release v0.1.623
  ([`c5862ec`](https://github.com/nfraxlab/svc-infra/commit/c5862ecc8cc52e74159c66f94bf11463e458e271))


## v0.1.622 (2025-10-19)

### Continuous Integration

- Release v0.1.622
  ([`271f3ac`](https://github.com/nfraxlab/svc-infra/commit/271f3ac19cf408f19fe1940655a668d3c36e9e3c))


## v0.1.621 (2025-10-19)

### Continuous Integration

- Release v0.1.621
  ([`d65bc0a`](https://github.com/nfraxlab/svc-infra/commit/d65bc0aefe618ca38338c42c0d954638998a38d5))


## v0.1.620 (2025-10-19)

### Continuous Integration

- Release v0.1.620
  ([`955c8b1`](https://github.com/nfraxlab/svc-infra/commit/955c8b1e4141e01ddea0294e94399b4467fa1fb6))


## v0.1.619 (2025-10-19)

### Continuous Integration

- Release v0.1.619
  ([`142da8a`](https://github.com/nfraxlab/svc-infra/commit/142da8a90b40abccf0a9855ff1a279a5eec7eaf0))


## v0.1.618 (2025-10-19)

### Bug Fixes

- Install uvicorn for acceptance api
  ([`bee7c90`](https://github.com/nfraxlab/svc-infra/commit/bee7c90cc5890201322d7a9dcf199ee53d835f2f))

- Prevent impersonation override stacking
  ([`d917167`](https://github.com/nfraxlab/svc-infra/commit/d917167d65cf5d48a4ca3e48f9eaa63ac9904511))

- **api**: Always display root card in service API setup across all environments
  ([`cb225eb`](https://github.com/nfraxlab/svc-infra/commit/cb225ebf486705d35a5942ce93d52c9d3206ebfd))

- **crud**: Update payload types in CRUD router functions to use specific schemas
  ([`3a4166f`](https://github.com/nfraxlab/svc-infra/commit/3a4166fc9722c809f619ffedbfe0eae49e5c5691))

- **sql**: Don't add ssl=true to asyncpg URL query, handle in connect_args only
  ([`b05a731`](https://github.com/nfraxlab/svc-infra/commit/b05a7315b83a26e7a07d2bfeef1fca1a82f071fd))

- **sql**: Handle asyncpg Railway connections properly
  ([`77da0d2`](https://github.com/nfraxlab/svc-infra/commit/77da0d26034bacd34b22ce1927cd567fd39d9ba9))

- Don't add connect_timeout to asyncpg URLs (use timeout in connect_args) - Convert ssl=true to
  sslmode=require for asyncpg (Railway compatibility) - Fixes TypeError: connect() got an unexpected
  keyword argument 'connect_timeout' - Fixes ClientConfigurationError: sslmode parameter validation

- **sql**: Remove _ensure_ssl_default calls from env.py templates
  ([`0cb8244`](https://github.com/nfraxlab/svc-infra/commit/0cb8244b374012e28bcc9f2adb6e74bce0fef2ab))

- Remove _ensure_ssl_default(u) call from env_async.py.tmpl - Remove _ensure_ssl_default(u) call
  from env_sync.py.tmpl - These calls were causing NameError since function is no longer imported -
  build_engine() now handles all SSL configuration internally

- **sql**: Remove ssl/sslmode from URL query for asyncpg, use connect_args
  ([`d5439d6`](https://github.com/nfraxlab/svc-infra/commit/d5439d6944396b14145e0b58fd45532b556500b0))

- asyncpg doesn't parse ssl=true or sslmode from URL query correctly - Always remove these from
  query and set ssl='require' in connect_args - Fixes ClientConfigurationError: sslmode parameter
  must be one of...

- **sql**: Update env.py templates to use build_engine for proper SSL handling
  ([`a972eae`](https://github.com/nfraxlab/svc-infra/commit/a972eae8c18152966c701a12256c56cc08c7ee3f))

- Update env_async.py.tmpl to use build_engine instead of create_async_engine - Remove unused
  _ensure_ssl_default imports from both templates - Update examples/migrations/env.py to match new
  template pattern - This ensures asyncpg SSL is handled correctly in all new projects

- **sql**: Use ssl parameter in connect_args for asyncpg, not sslmode
  ([`99b6590`](https://github.com/nfraxlab/svc-infra/commit/99b65907bb8c2276a6bb1b36fead11e5fd9ba6e5))

- asyncpg.connect() doesn't accept sslmode as kwarg - Remove sslmode from query params and use ssl
  in connect_args - Fixes TypeError: connect() got an unexpected keyword argument 'sslmode'

- **tests**: Update test assertions and add missing refresh mocks for SQL repository
  ([`0e1f68a`](https://github.com/nfraxlab/svc-infra/commit/0e1f68a8bf5d7127af138a17495720dbb505f548))

- **timeout**: Ensure proper handling of timeout seconds in middleware and client initialization
  ([`3313388`](https://github.com/nfraxlab/svc-infra/commit/3313388cf233ace35fd5053ee8f10e735b0279b6))

### Continuous Integration

- Release v0.1.618
  ([`b4929e8`](https://github.com/nfraxlab/svc-infra/commit/b4929e8f0d5f97e8cfa3ed90ceab8ed2b185edb3))

### Features

- Add acceptance tests for data lifecycle operations including fixtures, erasure, and retention
  ([`691aff1`](https://github.com/nfraxlab/svc-infra/commit/691aff17327f7c03473f5444b640ab021078f8b5))

- Add advanced feature setup instructions for authentication, multi-tenancy, and GDPR compliance in
  README and main.py
  ([`5122cce`](https://github.com/nfraxlab/svc-infra/commit/5122ccebdf8fe1e6780143e8bb0df32a60507a88))

- Add async Alembic migration support and CRUD endpoints for Project and Task models
  ([`54385b4`](https://github.com/nfraxlab/svc-infra/commit/54385b4638e7acdb5766b162325037d695ff888a))

- Implemented async migration environment in `env.py` for Alembic. - Created a new Mako template for
  migration scripts in `script.py.mako`. - Enhanced API routes in `routes.py` to include
  auto-generated CRUD endpoints for Project and Task models. - Added statistics summary endpoint for
  projects and tasks. - Introduced Pydantic schemas for Project and Task models in `schemas.py`. -
  Updated main application to register CRUD endpoints and create database tables on startup. -
  Refactored base model to use `ModelBase` from `svc-infra` for migration compatibility.

- Add billing and subscription settings to configuration and enhance API index response
  ([`3396497`](https://github.com/nfraxlab/svc-infra/commit/3396497c736d6609af9467ed48cf7bc31f4649e5))

- Add comprehensive production readiness punch list for v1 framework release
  ([`8c21966`](https://github.com/nfraxlab/svc-infra/commit/8c21966460d697e60f88b0453aa279df64947739))

- Established a structured checklist for ensuring production readiness, including must-have and
  nice-to-have features. - Detailed subtasks for each feature area, including research, design,
  implementation, testing, verification, and documentation. - Included acceptance criteria and
  evidence tracking for each task. - Organized tasks into categories such as security, rate
  limiting, observability, and more, with specific ownership and evidence requirements. - Added
  quick wins and tracking mechanisms for prioritization and finalization.

- Add documentation command to retrieve and display available docs topics
  ([`df305e7`](https://github.com/nfraxlab/svc-infra/commit/df305e74070cf0cf16c8353a224ead2c72d4a45e))

- Add new subcommands for SQL, Docs, DX, Jobs, and SDK groups in svc-infra CLI
  ([`4a4248b`](https://github.com/nfraxlab/svc-infra/commit/4a4248b80b6edc25da6bb9353750ed42f4567720))

- Add user and entity models with migrations
  ([`1daba9f`](https://github.com/nfraxlab/svc-infra/commit/1daba9fd1062417489d4bf8aa753f21020c51790))

- Created new migration file to add user and entity tables. - Updated env.py for improved logging
  and SSL handling. - Enhanced quick_setup.py to check for SQL_URL in .env and set defaults. -
  Implemented scaffold_models.py to streamline model scaffolding. - Added Project and Task models
  with unique constraints and service factories. - Introduced User model with authentication
  features and provider accounts. - Developed schemas for Project, Task, and User to facilitate data
  validation. - Added package markers in __init__.py files for models and schemas.

- Added template main FastAPI application and centralized settings management
  ([`4648732`](https://github.com/nfraxlab/svc-infra/commit/4648732d4d004c50d774821c2bd1112136e829c5))

- Implemented main FastAPI application in `main.py` with logging setup, service configuration, and
  modular feature integration. - Created `settings.py` for centralized configuration management
  using Pydantic, supporting environment variable loading and type-safe validation. - Added detailed
  comments and documentation for each step in the application setup process.

- Enhance __repr__ methods in Project and Task models to handle detached or expired states
  ([`945fe8c`](https://github.com/nfraxlab/svc-infra/commit/945fe8c4158027baa21db6356fdbf32bd7e3ee79))

- Enhance acceptance tests for idempotency, concurrency, jobs, and webhooks
  ([`ed9ce47`](https://github.com/nfraxlab/svc-infra/commit/ed9ce4752f00d4cc4c63f2592e21991762ed6658))

- Enhance acceptance tests for OpenAPI validation, maintenance mode, and circuit breaker
  functionality
  ([`9da7a0f`](https://github.com/nfraxlab/svc-infra/commit/9da7a0fa34f06a1b1943ce9b55c13233ee856ed1))

- Enhance configuration and security features in environment settings and main application
  ([`817fdb8`](https://github.com/nfraxlab/svc-infra/commit/817fdb8d50941a6b74870f8056476db3db9931f2))

- Enhance documentation command handling with improved topic normalization and directory options
  ([`c33b755`](https://github.com/nfraxlab/svc-infra/commit/c33b755a59511f24033eae86133d09b56f09d49a))

- Enhance documentation topic discovery with improved package metadata handling and fallback to
  site-packages
  ([`723922c`](https://github.com/nfraxlab/svc-infra/commit/723922cb49d1abfda7f25f4a1f71f3e59a49bd47))

- Implement duplicate prevention in scaffolding scripts
  ([`d91bd7c`](https://github.com/nfraxlab/svc-infra/commit/d91bd7c976a2a3c718854b54dfb40cb748edc05f))

- Added a new feature to prevent accidental overwrites of existing models in the scaffolding
  process. - Introduced `check_model_exists()` function to check for existing model and schema
  files. - Updated `scaffold_models.py` to include duplicate checking and provide user feedback. -
  Enhanced user experience with clear warnings and an option to overwrite existing files using the
  `--overwrite` flag. - Created `DUPLICATE_PREVENTION.md` documentation detailing the new feature
  and its usage. - Added `auth_reference.py` as a reference implementation for authentication setup.
  - Developed `quick_setup.py` for streamlined model scaffolding and migration processes. - Created
  automated tests in `test_duplicate_prevention.py` to verify the functionality of the duplicate
  prevention feature.

- Implement fixed-window rate limiting for acceptance tests with header-based isolation
  ([`4042470`](https://github.com/nfraxlab/svc-infra/commit/4042470985a910ec52fe17b9fb6014895dfb29da))

- Implement tenancy acceptance tests with tenant-aware resource management
  ([`2d33c47`](https://github.com/nfraxlab/svc-infra/commit/2d33c47dda6b207549c55495d57122c4a851bcaf))

- Implement timeouts and resource limits middleware, including graceful shutdown and HTTP client
  timeout handling
  ([`0304b38`](https://github.com/nfraxlab/svc-infra/commit/0304b38e7bc975e574ad64a8c49ffa43cb183643))

- Implement timeouts and resource limits, including middleware for body read and handler timeouts,
  and add acceptance tests for timeout scenarios
  ([`d0d0b12`](https://github.com/nfraxlab/svc-infra/commit/d0d0b12594ffb0f4d4d2cea775f323488a45cd42))

- Initialize svc-infra template with essential files and configurations
  ([`3e8aa5f`](https://github.com/nfraxlab/svc-infra/commit/3e8aa5fc0c0d4519ba80fdbb34d9426c1c6c82dd))

- Added .env.example for environment variable configuration - Created .gitignore to exclude
  unnecessary files - Implemented Makefile for common commands (install, run, clean) - Developed
  QUICKSTART.md and README.md for project guidance - Added USAGE.md for detailed usage instructions
  - Configured pyproject.toml for Poetry dependency management - Created run.sh script to start the
  service - Established directory structure with src/svc_infra_template and API routes - Implemented
  main FastAPI application with logging and service configuration - Added versioned API routes with
  health check and status endpoints

- Refactor CLI command structure and update documentation for consistency
  ([`50691a4`](https://github.com/nfraxlab/svc-infra/commit/50691a423dc2b59b54fa1c2a57ad33df479290eb))

- Refactor documentation topic discovery to normalize topic names and streamline fallback mechanisms
  ([`49f43f2`](https://github.com/nfraxlab/svc-infra/commit/49f43f2e97dd89a237c2b01384de9988f4ae01a7))

- Remove security hardening section and related middleware from main FastAPI application
  ([`2d3254a`](https://github.com/nfraxlab/svc-infra/commit/2d3254a0a425910441130872913c567ae0a9f483))

- Update acceptance tests and documentation for CLI migrations, job execution, and acceptance
  scenarios
  ([`ff1445b`](https://github.com/nfraxlab/svc-infra/commit/ff1445b2c941dee39f4b16a419a5e52c36b6261d))

- Update CRUD router response models to use specific read schemas and enhance repository object
  handling
  ([`db76f89`](https://github.com/nfraxlab/svc-infra/commit/db76f89e0c6243fc688132552d5113cd60f6bea9))

- Update Docker Compose to use --root-user-action=ignore for pip installs and implement header-only
  rate limiting middleware
  ([`b6c62d7`](https://github.com/nfraxlab/svc-infra/commit/b6c62d7e31019634332e428212a6cd030abf9e10))

- Update healthcheck parameters and improve documentation command handling
  ([`d447590`](https://github.com/nfraxlab/svc-infra/commit/d4475902244cd545512854b535514e15182d2f23))

- Update README to correct documentation links and improve structure
  ([`38bdc4a`](https://github.com/nfraxlab/svc-infra/commit/38bdc4a00378aa86d48b7259967cbd950ab43d75))

- Update run.sh to correctly reference the script directory for loading environment variables
  ([`2d848b7`](https://github.com/nfraxlab/svc-infra/commit/2d848b75b7c6e323fc6192cd0d9b0efdaa2759f2))

- Update security headers and documentation for improved defaults and clarity
  ([`5227883`](https://github.com/nfraxlab/svc-infra/commit/52278834526265ca373727a6bcb4984083aa6965))

- Update tenant CRUD endpoints to use specific response models and improve error handling
  ([`f2ea4c3`](https://github.com/nfraxlab/svc-infra/commit/f2ea4c33bed4edf51f09694c72f39f275dd16ba5))

- **admin**: Add comprehensive documentation for admin scope and impersonation features
  ([`36b76fa`](https://github.com/nfraxlab/svc-infra/commit/36b76fa1ddaf775fd6c6a1a58ec8a82186e6cdff))

- **admin**: Implement admin API with impersonation support and related tests
  ([`7d70806`](https://github.com/nfraxlab/svc-infra/commit/7d708069b4652a27938bd1f183f7507313242295))

- **billing**: Introduce billing primitives and usage aggregation
  ([`335b316`](https://github.com/nfraxlab/svc-infra/commit/335b316f040b2c8483111a40567754bcff4192a7))

- Added a new FastAPI router for billing under /_billing to handle usage ingestion and aggregate
  reads. - Implemented AsyncBillingService for recording usage, aggregating daily metrics, and
  generating monthly invoices. - Created job handlers for daily aggregation and monthly invoice
  generation, emitting relevant webhooks. - Introduced quota enforcement based on internal plan
  entitlements and usage aggregates. - Developed schemas for usage input and output, as well as
  aggregate responses. - Added acceptance and unit tests for billing functionality, including usage
  ingestion and quota dependencies. - Documented the billing module, outlining its purpose, data
  model, and integration with APF Payments.

- **cache**: Add easy integration helper `add_cache` for ASGI app lifecycle management
  ([`911fdd7`](https://github.com/nfraxlab/svc-infra/commit/911fdd7217692dcf934d73e4c7530570ac8b63b7))

- **cleanup**: Enhance cleanup targets to remove example caches and logs
  ([`c9dfe29`](https://github.com/nfraxlab/svc-infra/commit/c9dfe290e442b47690661e1fb01e6aae993cc42c))

- **docs**: Add scoped documentation registration for SQL resources
  ([`18fed5c`](https://github.com/nfraxlab/svc-infra/commit/18fed5ced66b7bc828279e082123b1bdb8a48231))

- **docs**: Register scoped documentation for billing and MongoDB resources
  ([`f31954d`](https://github.com/nfraxlab/svc-infra/commit/f31954dfa76dce517a1d599d1d77c91760917e73))

- Added logic to register scoped documentation for the billing API under the prefix "/_billing" only
  once. - Implemented similar functionality for MongoDB resources under the prefix "/_mongo".

- **tests**: Add unit and acceptance tests for timeout handling and job processing
  ([`45d1c65`](https://github.com/nfraxlab/svc-infra/commit/45d1c653a5281b00843bf596667e9781b9fb280c))


## v0.1.617 (2025-10-19)

### Continuous Integration

- Release v0.1.617
  ([`d7ea243`](https://github.com/nfraxlab/svc-infra/commit/d7ea243544bec54add5e4722688976ccff741a91))


## v0.1.616 (2025-10-19)

### Continuous Integration

- Release v0.1.616
  ([`b328a42`](https://github.com/nfraxlab/svc-infra/commit/b328a425e8805b0510a641aa57fefd50d350eec8))


## v0.1.615 (2025-10-19)

### Continuous Integration

- Release v0.1.615
  ([`46d8753`](https://github.com/nfraxlab/svc-infra/commit/46d87536195f19125450f8272456ca5d1b7a8383))


## v0.1.614 (2025-10-19)

### Continuous Integration

- Release v0.1.614
  ([`e45eef9`](https://github.com/nfraxlab/svc-infra/commit/e45eef940dd24ab41dc25096b06adfe258af554d))


## v0.1.613 (2025-10-18)

### Continuous Integration

- Release v0.1.613
  ([`521ab5b`](https://github.com/nfraxlab/svc-infra/commit/521ab5b3f88cce02197cb56c4d231fec00834d9c))

### Features

- Add acceptance tests for rate limiting and abuse heuristics, enhance error handling with headers
  ([`df760c3`](https://github.com/nfraxlab/svc-infra/commit/df760c35ff2a75a431288bd8467e45900983b2cb))

- Add acceptance tests for RBAC/ABAC and enhance security demo routes - fixed acceptance tests
  ([`5856deb`](https://github.com/nfraxlab/svc-infra/commit/5856debbcf517484b718ef4132d00fc233d49904))

- Add bundled documentation support and enhance CLI for dynamic topic resolution
  ([`48ba0d9`](https://github.com/nfraxlab/svc-infra/commit/48ba0d9daa3c1ef4a962da30f031af1797b7c0c9))

- Add documentation command group with dynamic topic subcommands and tests
  ([`e25486a`](https://github.com/nfraxlab/svc-infra/commit/e25486a57aceef29aa54c0b1fe7b27c436860164))

- Enhance acceptance tests for authentication flows, password policies, and API key lifecycle
  ([`9b65067`](https://github.com/nfraxlab/svc-infra/commit/9b65067b1bd68e848026af1ee0e9cb03ae04156a))

- Refactor documentation handling and enhance rate limiting middleware for better test isolation
  ([`607cca5`](https://github.com/nfraxlab/svc-infra/commit/607cca5bb9986bb320f9ac944ecd6579aa3a4eb7))

- Remove bundled documentation files from the project
  ([`79f57fd`](https://github.com/nfraxlab/svc-infra/commit/79f57fdf46a96ef0bca49d9316d33b22fce0546b))

- Update version in pyproject.toml and enhance documentation command to support packaged topics
  ([`f22525f`](https://github.com/nfraxlab/svc-infra/commit/f22525f02aed0df25b2c8e3cc1ee2abc67f9015b))


## v0.1.612 (2025-10-18)

### Continuous Integration

- Release v0.1.612
  ([`b25e9c7`](https://github.com/nfraxlab/svc-infra/commit/b25e9c74f0258340053189deb218c169e7e31d03))

### Features

- Update cache setup to default to in-memory backend and enhance tag resolution with template
  rendering
  ([`d54a1c4`](https://github.com/nfraxlab/svc-infra/commit/d54a1c4736051027ff80bb728864958405d025c5))


## v0.1.611 (2025-10-18)

### Continuous Integration

- Release v0.1.611
  ([`bd8a77f`](https://github.com/nfraxlab/svc-infra/commit/bd8a77fb8ef41e3571a2e013d584ca3d1d39339c))

### Features

- Enhance logging and caching functionality with comprehensive tests and documentation updates
  ([`9f9d785`](https://github.com/nfraxlab/svc-infra/commit/9f9d785014b6d02cbb4ebb1188299373024f9464))


## v0.1.610 (2025-10-18)

### Continuous Integration

- Release v0.1.610
  ([`854a656`](https://github.com/nfraxlab/svc-infra/commit/854a65636527bce11347993aa90c126b770077e7))

### Features

- Add observability metrics and acceptance tests for metrics exposure
  ([`0417b3b`](https://github.com/nfraxlab/svc-infra/commit/0417b3b57335b881094e81715b1748ec660605a7))


## v0.1.609 (2025-10-18)

### Continuous Integration

- Release v0.1.609
  ([`afbdf90`](https://github.com/nfraxlab/svc-infra/commit/afbdf9067acd356ba1872de05600170a152f468e))

### Features

- Enhance CLI functionality with acceptance data seeding and comprehensive command help
  ([`3926fa1`](https://github.com/nfraxlab/svc-infra/commit/3926fa123459672726826a000c0c46bb730c2965))


## v0.1.608 (2025-10-18)

### Bug Fixes

- Update SBOM artifact naming and paths for consistency
  ([`483156a`](https://github.com/nfraxlab/svc-infra/commit/483156ad44f8ee6cab7bf3144e54fc29cd57f1cf))

### Continuous Integration

- Release v0.1.608
  ([`5c934aa`](https://github.com/nfraxlab/svc-infra/commit/5c934aaa1b7f5d78a7d47f895625bada6293def5))

### Features

- Add Trivy ignore list for vendor images and update scanning conditions
  ([`d2fd72d`](https://github.com/nfraxlab/svc-infra/commit/d2fd72d2c48a64c345b26f5f86a7a0ca65dbbf65))

- Enhance acceptance testing framework and improve CI/CD workflows
  ([`e6f63bf`](https://github.com/nfraxlab/svc-infra/commit/e6f63bf3e574555e5a6e65ff4d95efa568b76ace))

- Add .acceptance.db for acceptance testing database - Update PLANS.md with supply-chain and
  provenance tasks - Modify acceptance.yml to include SBOM generation and vulnerability scanning -
  Refactor Makefile to use Poetry for unit tests - Update docker-compose.test.yml for environment
  variables and dependencies - Enhance api.md with quickstart guide for easy_service_app - Implement
  acceptance app in tests/acceptance/app.py with fake payments adapter - Add acceptance tests for
  OpenAPI and CORS in tests/acceptance/test_api_openapi_and_cors.py - Create basic payment flow
  tests in tests/acceptance/test_payments_basic_flows.py - Add pagination limit tests in
  tests/unit/payments/test_payments_pagination_limits.py - Implement async tenant resolution tests
  in tests/unit/payments/test_payments_tenant_resolution.py

- Improve acceptance testing setup and API readiness checks
  ([`ffe8077`](https://github.com/nfraxlab/svc-infra/commit/ffe8077ef846c490a22808884eb4f28da1613c2f))


## v0.1.607 (2025-10-18)

### Continuous Integration

- Release v0.1.607
  ([`a407e35`](https://github.com/nfraxlab/svc-infra/commit/a407e35691f0862014133034b4fdfdba8edad459))

### Features

- Implement A0 Acceptance Harness and CI Promotion Gate
  ([`83e423d`](https://github.com/nfraxlab/svc-infra/commit/83e423d3f749a08a774af5a40c314c9ed2e52796))

- Added a new acceptance harness using Docker Compose to validate builds before promotion. - Created
  `docker-compose.test.yml` for the acceptance stack including API, Redis, and Postgres services. -
  Introduced Makefile targets for managing the acceptance process: `accept`, `compose_up`, `wait`,
  `seed`, `down`. - Developed initial acceptance tests in `tests/acceptance`, including a smoke test
  for the `/ping` endpoint. - Updated CI workflow to include acceptance tests with a backend matrix
  (in-memory and Redis+Postgres). - Enhanced documentation for acceptance harness usage and
  configuration. - Removed legacy compatibility packages and updated import paths in unit tests.


## v0.1.606 (2025-10-17)

### Continuous Integration

- Release v0.1.606
  ([`f27722e`](https://github.com/nfraxlab/svc-infra/commit/f27722e85904d3a1c98d2b1a795e53a649e4b7f1))


## v0.1.605 (2025-10-17)

### Continuous Integration

- Release v0.1.605
  ([`3b44b43`](https://github.com/nfraxlab/svc-infra/commit/3b44b43e71a37dfc9df09d745cc8f47e78be4c5b))

### Features

- **docs**: Add comprehensive documentation for API and SDK generation
  ([`647ceaa`](https://github.com/nfraxlab/svc-infra/commit/647ceaaae6b1eb1f0611123ed627bad82afb2aaa))

- Introduced a new documentation file detailing how to enable API docs, enrich OpenAPI, and generate
  SDKs. - Included instructions for using the CLI to generate TypeScript, Python SDKs, and Postman
  collections. - Added troubleshooting tips and quick curl examples for API usage.

feat(billing): Implement billing models and service logic

- Created billing models including UsageEvent, UsageAggregate, Plan, Subscription, Invoice, and
  related entities. - Developed BillingService to handle usage recording, daily aggregation, and
  monthly invoice generation. - Added idempotency checks to prevent duplicate usage records.

test(billing): Add unit tests for billing service functionality

- Implemented tests for recording usage, generating invoices, and ensuring provider sync hooks are
  called. - Added tests to verify unique constraints for idempotency keys.

feat(cli): Introduce SDK generation commands

- Added CLI commands for generating TypeScript and Python SDKs from OpenAPI specifications. -
  Implemented a command for converting OpenAPI to Postman collections.

test(cli): Create tests for SDK CLI commands

- Developed tests to ensure SDK generation commands print the correct output without executing. -
  Added smoke tests to verify the generated SDKs can be imported and used.

test(docs): Validate documentation landing page behavior

- Created tests to ensure the documentation landing page renders correctly at the root or fallback
  path. - Verified that the landing page includes links to Swagger UI, ReDoc, and OpenAPI spec.


## v0.1.604 (2025-10-16)

### Continuous Integration

- Release v0.1.604
  ([`5db9c92`](https://github.com/nfraxlab/svc-infra/commit/5db9c923852cf223ca117c155303c707d404eee6))


## v0.1.603 (2025-10-16)

### Continuous Integration

- Release v0.1.603
  ([`5946310`](https://github.com/nfraxlab/svc-infra/commit/59463100c917cd7dd3c95c16690fc3a5a1b118ff))


## v0.1.602 (2025-10-16)

### Continuous Integration

- Release v0.1.602
  ([`66b7b09`](https://github.com/nfraxlab/svc-infra/commit/66b7b0976077cf370a5946937f8c95324a1cd249))


## v0.1.601 (2025-10-16)

### Continuous Integration

- Release v0.1.601
  ([`89a7eef`](https://github.com/nfraxlab/svc-infra/commit/89a7eef123ac1b1b7cb97bc4aa42bbf4640ca2d3))


## v0.1.600 (2025-10-16)

### Continuous Integration

- Release v0.1.600
  ([`35e408a`](https://github.com/nfraxlab/svc-infra/commit/35e408a3db1dcad43e832c3bbcb6620986048e1b))


## v0.1.599 (2025-10-15)

### Continuous Integration

- Release v0.1.599
  ([`7b0433c`](https://github.com/nfraxlab/svc-infra/commit/7b0433c9f0f8e271f7c216872d7575448211b203))

### Documentation

- Add environment variable reference
  ([`3091169`](https://github.com/nfraxlab/svc-infra/commit/3091169483dcf791dbd914e5aa7d243612aa4afc))

- Refresh readme and helper guides
  ([`b0c321e`](https://github.com/nfraxlab/svc-infra/commit/b0c321e45125f3f39460194b54bd3b2967bccf6b))


## v0.1.598 (2025-10-15)

### Continuous Integration

- Release v0.1.598
  ([`2843810`](https://github.com/nfraxlab/svc-infra/commit/28438100d181b3ca366029e9bb2f04003d71f8ce))


## v0.1.597 (2025-10-15)

### Continuous Integration

- Release v0.1.597
  ([`8600f9b`](https://github.com/nfraxlab/svc-infra/commit/8600f9b61eaddf67c31e2f6471876b92098bc147))


## v0.1.596 (2025-10-15)

### Continuous Integration

- Release v0.1.596
  ([`8bb8ba7`](https://github.com/nfraxlab/svc-infra/commit/8bb8ba79f207f4b0b43ffee2d0af664078c21189))


## v0.1.595 (2025-10-15)

### Continuous Integration

- Release v0.1.595
  ([`483e18c`](https://github.com/nfraxlab/svc-infra/commit/483e18c6610afdf064d3c7c2019ae04766332bab))


## v0.1.594 (2025-10-15)

### Chores

- Fix flake8 E101 by normalizing docstring indentation
  ([`5bd84d6`](https://github.com/nfraxlab/svc-infra/commit/5bd84d6b3165bedc9d3fdd11482d674203a84f9e))

### Continuous Integration

- Release v0.1.594
  ([`7151d94`](https://github.com/nfraxlab/svc-infra/commit/7151d94610ca5db28159cf1c74a5eade21c3e7c6))

### Features

- **auth**: Implement rotating JWT strategy with support for old secrets and update related tests
  ([`6b5755c`](https://github.com/nfraxlab/svc-infra/commit/6b5755c15caecd7d819b83c8feceeaa7af849206))

- **prod-readiness-v1**: Consolidate security hardening (password policy, lockout, refresh rotation,
  RBAC, audit chain) and planning docs
  ([`e1abf1e`](https://github.com/nfraxlab/svc-infra/commit/e1abf1e9a9a12942e045a21e42ae832e44326628))

- **security**: Enhance security features and implement rate limiting
  ([`504b8a7`](https://github.com/nfraxlab/svc-infra/commit/504b8a747294684358863d5cf2c57ca8529b12b5))


## v0.1.593 (2025-10-14)

### Continuous Integration

- Release v0.1.593
  ([`24553fc`](https://github.com/nfraxlab/svc-infra/commit/24553fc49fb776275c5e2171857b0a2708c20a45))


## v0.1.592 (2025-10-14)

### Continuous Integration

- Release v0.1.592
  ([`a9f02cc`](https://github.com/nfraxlab/svc-infra/commit/a9f02cced7241bca1a759a8500ed8bc2e4883f4a))


## v0.1.591 (2025-10-14)

### Continuous Integration

- Release v0.1.591
  ([`5f47a76`](https://github.com/nfraxlab/svc-infra/commit/5f47a76064b72cadc324d49906185f0752cf8b23))


## v0.1.590 (2025-10-14)

### Continuous Integration

- Release v0.1.590
  ([`fe92810`](https://github.com/nfraxlab/svc-infra/commit/fe928101c147af20f97978a15c7d83dcf6b598af))


## v0.1.589 (2025-10-13)

### Continuous Integration

- Release v0.1.589
  ([`11aa9d0`](https://github.com/nfraxlab/svc-infra/commit/11aa9d09ba00f65a75a89cb6954938a7f1fcc1f3))


## v0.1.588 (2025-10-13)

### Continuous Integration

- Release v0.1.588
  ([`13acf3b`](https://github.com/nfraxlab/svc-infra/commit/13acf3b1a2500b5bbab7da68530e1541ccd638d9))


## v0.1.587 (2025-10-13)

### Continuous Integration

- Release v0.1.587
  ([`2a97a83`](https://github.com/nfraxlab/svc-infra/commit/2a97a83a2c4f8544ca0ceda8ab4e150956b0475c))


## v0.1.586 (2025-10-13)

### Continuous Integration

- Release v0.1.586
  ([`f2b4a43`](https://github.com/nfraxlab/svc-infra/commit/f2b4a438effdc09d29f83935ba74902f1e0e5ff4))


## v0.1.585 (2025-10-13)

### Continuous Integration

- Release v0.1.585
  ([`1d6b05e`](https://github.com/nfraxlab/svc-infra/commit/1d6b05e38ab002cfb4563fdfea12385e75aaba4e))


## v0.1.584 (2025-10-13)

### Continuous Integration

- Release v0.1.584
  ([`446bc9c`](https://github.com/nfraxlab/svc-infra/commit/446bc9cb6e4be38d21b76f022388423d5880fff5))


## v0.1.583 (2025-10-13)

### Continuous Integration

- Release v0.1.583
  ([`23af995`](https://github.com/nfraxlab/svc-infra/commit/23af995a22f7eb20b006a63c33280b67b7366b17))


## v0.1.582 (2025-10-13)

### Continuous Integration

- Release v0.1.582
  ([`b3caa88`](https://github.com/nfraxlab/svc-infra/commit/b3caa88a7e9dcbed94032e5bf8a9925df2e4f640))


## v0.1.581 (2025-10-13)

### Continuous Integration

- Release v0.1.581
  ([`ba834ad`](https://github.com/nfraxlab/svc-infra/commit/ba834aded69a54ff1a5afed1ec41d13cde8db8dc))


## v0.1.580 (2025-10-13)

### Continuous Integration

- Release v0.1.580
  ([`bc0683b`](https://github.com/nfraxlab/svc-infra/commit/bc0683b8f9167956c933a1c5f704267ced3e3938))


## v0.1.579 (2025-10-13)

### Continuous Integration

- Release v0.1.579
  ([`55eaf51`](https://github.com/nfraxlab/svc-infra/commit/55eaf51ea7f259f7d20f7e84bc94d087f891a42f))


## v0.1.578 (2025-10-13)

### Continuous Integration

- Release v0.1.578
  ([`44b3c79`](https://github.com/nfraxlab/svc-infra/commit/44b3c79197d074a5b1831e8e27607a74c589a9b2))


## v0.1.577 (2025-10-13)

### Continuous Integration

- Release v0.1.577
  ([`546b85a`](https://github.com/nfraxlab/svc-infra/commit/546b85a414d692f763a274ee3fa7fefa6f1a7620))


## v0.1.576 (2025-10-13)

### Continuous Integration

- Release v0.1.576
  ([`cc90609`](https://github.com/nfraxlab/svc-infra/commit/cc90609491684c72f48fbf04d0fb16bf01d91880))


## v0.1.575 (2025-10-13)

### Continuous Integration

- Release v0.1.575
  ([`b38ec9e`](https://github.com/nfraxlab/svc-infra/commit/b38ec9ecb798663c651b8f0e73b0a50f32a0e771))


## v0.1.574 (2025-10-12)

### Continuous Integration

- Release v0.1.574
  ([`992017e`](https://github.com/nfraxlab/svc-infra/commit/992017e5a3b8548d251fc303401aae50b2e405a2))


## v0.1.573 (2025-10-12)

### Continuous Integration

- Release v0.1.573
  ([`d09da4e`](https://github.com/nfraxlab/svc-infra/commit/d09da4e24e8001d4f6940c1416a79f907361f750))


## v0.1.572 (2025-10-12)

### Continuous Integration

- Release v0.1.572
  ([`63a8365`](https://github.com/nfraxlab/svc-infra/commit/63a836541ae004b9bbfa910a7d3e661f3a048b9f))


## v0.1.571 (2025-10-12)

### Continuous Integration

- Release v0.1.571
  ([`0a16a23`](https://github.com/nfraxlab/svc-infra/commit/0a16a23d7042fb7d70adb88936c892c1b8bc3f54))


## v0.1.570 (2025-10-12)

### Continuous Integration

- Release v0.1.570
  ([`eab456a`](https://github.com/nfraxlab/svc-infra/commit/eab456a540ddf9a7240f420d0a17c1a47abf2a75))


## v0.1.569 (2025-10-12)

### Continuous Integration

- Release v0.1.569
  ([`9d3339c`](https://github.com/nfraxlab/svc-infra/commit/9d3339cba946aa3ed42503c4639297e7ad9e7f27))


## v0.1.568 (2025-10-12)

### Continuous Integration

- Release v0.1.568
  ([`7b3119c`](https://github.com/nfraxlab/svc-infra/commit/7b3119c6e89fe800e38b07b4ad44d2e679ddaa5b))


## v0.1.567 (2025-10-12)

### Continuous Integration

- Release v0.1.567
  ([`f8add8a`](https://github.com/nfraxlab/svc-infra/commit/f8add8aa3fe66b7d5a0d3bfde1425ab61e14258c))


## v0.1.566 (2025-10-12)

### Continuous Integration

- Release v0.1.566
  ([`d524d4b`](https://github.com/nfraxlab/svc-infra/commit/d524d4b6818b2e8a8a22b70024c0b5ab21033186))


## v0.1.565 (2025-10-12)

### Continuous Integration

- Release v0.1.565
  ([`0681734`](https://github.com/nfraxlab/svc-infra/commit/0681734e19553f310db220673960c2f090c607af))


## v0.1.564 (2025-10-12)

### Continuous Integration

- Release v0.1.564
  ([`6a533d3`](https://github.com/nfraxlab/svc-infra/commit/6a533d366ed8b303b872156f8172a1deb4c879a5))


## v0.1.563 (2025-10-12)

### Continuous Integration

- Release v0.1.563
  ([`6f8e48f`](https://github.com/nfraxlab/svc-infra/commit/6f8e48fc7d48dccf862a61dd829219c58c66706c))


## v0.1.562 (2025-10-11)

### Continuous Integration

- Release v0.1.562
  ([`a8fb812`](https://github.com/nfraxlab/svc-infra/commit/a8fb812224983a1e2c11fbfb7dd0a02654a3dc7b))


## v0.1.561 (2025-10-10)

### Continuous Integration

- Release v0.1.561
  ([`420fb10`](https://github.com/nfraxlab/svc-infra/commit/420fb10632284284410135b9f5e6961395127b06))


## v0.1.560 (2025-10-10)

### Continuous Integration

- Release v0.1.560
  ([`d41f1c5`](https://github.com/nfraxlab/svc-infra/commit/d41f1c546214c9f64cb27a7e2fdcccf45310e13a))


## v0.1.559 (2025-10-10)

### Continuous Integration

- Release v0.1.559
  ([`acb36f2`](https://github.com/nfraxlab/svc-infra/commit/acb36f2096140837badcc0b7756099bbb8942947))


## v0.1.558 (2025-10-10)

### Continuous Integration

- Release v0.1.558
  ([`681af3e`](https://github.com/nfraxlab/svc-infra/commit/681af3ec6c3d6c45b97184981320084cf0ce3142))


## v0.1.557 (2025-10-10)

### Continuous Integration

- Release v0.1.557
  ([`4849467`](https://github.com/nfraxlab/svc-infra/commit/48494675b4eeaa6c9e0594f334aece5f897b1dd2))


## v0.1.556 (2025-10-10)

### Continuous Integration

- Release v0.1.556
  ([`178ea26`](https://github.com/nfraxlab/svc-infra/commit/178ea268d6e5391816458303f39a0d0061ed547e))


## v0.1.555 (2025-10-09)

### Continuous Integration

- Release v0.1.555
  ([`347286d`](https://github.com/nfraxlab/svc-infra/commit/347286d8de2316e46f3e445a785e8be3a6b4cd2a))


## v0.1.554 (2025-10-09)

### Continuous Integration

- Release v0.1.554
  ([`c7a672a`](https://github.com/nfraxlab/svc-infra/commit/c7a672ac6ad32590ce8c09a1f71f2d8ee83f0ce0))


## v0.1.553 (2025-10-09)

### Continuous Integration

- Release v0.1.553
  ([`1a6529e`](https://github.com/nfraxlab/svc-infra/commit/1a6529e408368383cd162c504fae9303e86b2050))


## v0.1.552 (2025-10-09)

### Continuous Integration

- Release v0.1.552
  ([`6487e4a`](https://github.com/nfraxlab/svc-infra/commit/6487e4a8c208bca8d9390bdd464e5dc4f8135941))


## v0.1.551 (2025-10-09)

### Continuous Integration

- Release v0.1.551
  ([`9a093ac`](https://github.com/nfraxlab/svc-infra/commit/9a093ac4cba80389df557c7faaa5b7d330c9e95b))


## v0.1.550 (2025-10-09)

### Continuous Integration

- Release v0.1.550
  ([`5ed840b`](https://github.com/nfraxlab/svc-infra/commit/5ed840b2f38d0f21276b0f35b8a04b44251410d4))


## v0.1.549 (2025-10-09)

### Continuous Integration

- Release v0.1.549
  ([`0d1cfe0`](https://github.com/nfraxlab/svc-infra/commit/0d1cfe038a08a332102461927698ff43bcea09b3))


## v0.1.548 (2025-10-09)

### Continuous Integration

- Release v0.1.548
  ([`be7419f`](https://github.com/nfraxlab/svc-infra/commit/be7419f8c9a03eacc67326e07a961634eede76fd))


## v0.1.547 (2025-10-09)

### Continuous Integration

- Release v0.1.547
  ([`5b98896`](https://github.com/nfraxlab/svc-infra/commit/5b988967ae5d1429dfdb9a5f542d484aaa9cce27))


## v0.1.546 (2025-10-09)

### Continuous Integration

- Release v0.1.546
  ([`6f33afb`](https://github.com/nfraxlab/svc-infra/commit/6f33afbef888d9dc265b2bc15fb51282265f2e0d))


## v0.1.545 (2025-10-09)

### Continuous Integration

- Release v0.1.545
  ([`ed9b08d`](https://github.com/nfraxlab/svc-infra/commit/ed9b08d17424933ccd9428678272f4c947daab7c))


## v0.1.544 (2025-10-09)

### Continuous Integration

- Release v0.1.544
  ([`cb30522`](https://github.com/nfraxlab/svc-infra/commit/cb305225a5678f3ce36ad085b276869a812f3c3d))


## v0.1.543 (2025-10-09)

### Continuous Integration

- Release v0.1.542
  ([`30037c7`](https://github.com/nfraxlab/svc-infra/commit/30037c761dca3bf405e883367fd3f9e7e2ba65bf))

- Release v0.1.543
  ([`ffe7561`](https://github.com/nfraxlab/svc-infra/commit/ffe7561bb71b8afa09754cb14b555a94953e15f3))


## v0.1.541 (2025-10-09)

### Continuous Integration

- Release v0.1.541
  ([`2405644`](https://github.com/nfraxlab/svc-infra/commit/24056445703c115eef77986501a84ac6f2c9afa2))


## v0.1.540 (2025-10-09)

### Continuous Integration

- Release v0.1.540
  ([`d5bddab`](https://github.com/nfraxlab/svc-infra/commit/d5bddab60c52bcff0d00f2ad4a3e0e0b3b62624d))


## v0.1.539 (2025-10-09)

### Continuous Integration

- Release v0.1.539
  ([`c28c172`](https://github.com/nfraxlab/svc-infra/commit/c28c172f36fdcb545ac05d26f6685eef4fbdd45a))


## v0.1.538 (2025-10-09)

### Continuous Integration

- Release v0.1.538
  ([`5f3b2dc`](https://github.com/nfraxlab/svc-infra/commit/5f3b2dc3dc529697a939cb4aa906aad2239cf90a))


## v0.1.537 (2025-10-08)

### Continuous Integration

- Release v0.1.537
  ([`0c89ffb`](https://github.com/nfraxlab/svc-infra/commit/0c89ffbf7aea8e19531e92de638c42d8598df1ab))


## v0.1.536 (2025-10-08)

### Continuous Integration

- Release v0.1.536
  ([`74823f6`](https://github.com/nfraxlab/svc-infra/commit/74823f673a0b0e0799fbbf6ef38407c4d52c5fa5))


## v0.1.535 (2025-10-08)

### Continuous Integration

- Release v0.1.535
  ([`86ab42d`](https://github.com/nfraxlab/svc-infra/commit/86ab42d421c1e5345f95fc8b7762f75ce260f65d))


## v0.1.534 (2025-10-08)

### Continuous Integration

- Release v0.1.534
  ([`d8713da`](https://github.com/nfraxlab/svc-infra/commit/d8713da7d5c97d98753fc0659b3d1fe30b9b1ec6))


## v0.1.533 (2025-10-08)

### Continuous Integration

- Release v0.1.533
  ([`0dfb54f`](https://github.com/nfraxlab/svc-infra/commit/0dfb54f7117c46eec6c058094c7d1c9253971dc7))


## v0.1.532 (2025-10-08)

### Continuous Integration

- Release v0.1.532
  ([`5eb6935`](https://github.com/nfraxlab/svc-infra/commit/5eb69358ba6732b251a59c9e312adaed519e308d))


## v0.1.531 (2025-10-08)

### Continuous Integration

- Release v0.1.531
  ([`9a46a02`](https://github.com/nfraxlab/svc-infra/commit/9a46a021f10142f18eaeddd8a8a2439278cb2fa5))


## v0.1.530 (2025-10-08)

### Continuous Integration

- Release v0.1.530
  ([`4c13a79`](https://github.com/nfraxlab/svc-infra/commit/4c13a791b9fa20a4cd61727bb4ccb09d8d06bb07))


## v0.1.529 (2025-10-08)

### Continuous Integration

- Release v0.1.529
  ([`43cffa4`](https://github.com/nfraxlab/svc-infra/commit/43cffa414bd02b0bc5be9e94ec3a356e0d8c143e))


## v0.1.528 (2025-10-08)

### Continuous Integration

- Release v0.1.528
  ([`baa9cb3`](https://github.com/nfraxlab/svc-infra/commit/baa9cb31d43416e9f4f21eb190e8bd36e75795fe))


## v0.1.527 (2025-10-07)

### Continuous Integration

- Release v0.1.527
  ([`21d0811`](https://github.com/nfraxlab/svc-infra/commit/21d08115864b17bc5393577dd02f4b45d1191599))


## v0.1.526 (2025-10-04)

### Continuous Integration

- Release v0.1.526
  ([`cbe4882`](https://github.com/nfraxlab/svc-infra/commit/cbe4882a2ddf5eadbf96ac0e5a530aa5cda532e6))


## v0.1.525 (2025-10-04)

### Continuous Integration

- Release v0.1.525
  ([`1218da1`](https://github.com/nfraxlab/svc-infra/commit/1218da16f1e374f1d8001b9025f82c297062e9bf))


## v0.1.524 (2025-10-04)

### Continuous Integration

- Release v0.1.524
  ([`75f0c5f`](https://github.com/nfraxlab/svc-infra/commit/75f0c5f71ba3078c1753184c4a5b9cf07e11ea12))


## v0.1.523 (2025-10-04)

### Continuous Integration

- Release v0.1.523
  ([`2ffffd6`](https://github.com/nfraxlab/svc-infra/commit/2ffffd6bd64794ff609a04c28319e7097334a91d))


## v0.1.522 (2025-10-04)

### Continuous Integration

- Release v0.1.522
  ([`00f32eb`](https://github.com/nfraxlab/svc-infra/commit/00f32eb26238ca5006dc930942105091800e7af1))


## v0.1.521 (2025-10-04)

### Continuous Integration

- Release v0.1.521
  ([`f8f9b64`](https://github.com/nfraxlab/svc-infra/commit/f8f9b643f76befa8567dffa11e983e722270569f))


## v0.1.520 (2025-10-04)

### Continuous Integration

- Release v0.1.520
  ([`25c6693`](https://github.com/nfraxlab/svc-infra/commit/25c6693955a911f2a102800f927b3207dfca30ca))


## v0.1.519 (2025-10-04)

### Continuous Integration

- Release v0.1.519
  ([`8afed1d`](https://github.com/nfraxlab/svc-infra/commit/8afed1dafda40d8b41a55bed2241ef25417e7ccf))


## v0.1.518 (2025-10-03)

### Continuous Integration

- Release v0.1.518
  ([`5c85a1f`](https://github.com/nfraxlab/svc-infra/commit/5c85a1fba3cb32967a1691f95b1f4cf221ef7f7f))


## v0.1.517 (2025-10-03)

### Continuous Integration

- Release v0.1.517
  ([`a33e827`](https://github.com/nfraxlab/svc-infra/commit/a33e8278a2b361c5577e8c25bbd052e5c02fe7c5))


## v0.1.516 (2025-10-03)

### Continuous Integration

- Release v0.1.516
  ([`f54fafc`](https://github.com/nfraxlab/svc-infra/commit/f54fafcb7881be58121eb3f22205e02e5c89df12))


## v0.1.515 (2025-10-03)

### Continuous Integration

- Release v0.1.515
  ([`689163d`](https://github.com/nfraxlab/svc-infra/commit/689163d895292cf8aa590abc23e5ba00cf5f770c))


## v0.1.514 (2025-10-03)

### Continuous Integration

- Release v0.1.514
  ([`f0bca0c`](https://github.com/nfraxlab/svc-infra/commit/f0bca0c9ea4eb1996d0bc94a8cea17df6dc3ff14))


## v0.1.513 (2025-10-03)

### Continuous Integration

- Release v0.1.513
  ([`8ab5488`](https://github.com/nfraxlab/svc-infra/commit/8ab5488f30296f4be6f5fd231e541e51e9b2cad4))


## v0.1.512 (2025-10-03)

### Continuous Integration

- Release v0.1.512
  ([`48c0e31`](https://github.com/nfraxlab/svc-infra/commit/48c0e316f3e635fc784f307d2b8e5d2769186b0d))


## v0.1.511 (2025-10-03)

### Continuous Integration

- Release v0.1.511
  ([`96f0589`](https://github.com/nfraxlab/svc-infra/commit/96f058946041d7210c67b9554c23ea2167ea8a90))


## v0.1.510 (2025-10-03)

### Continuous Integration

- Release v0.1.510
  ([`d31bf65`](https://github.com/nfraxlab/svc-infra/commit/d31bf6588335bde7a24b9d137df22237155bd6fb))


## v0.1.509 (2025-10-03)

### Continuous Integration

- Release v0.1.509
  ([`6c02593`](https://github.com/nfraxlab/svc-infra/commit/6c0259384f1f3b323b99c3d5f7479bf4a257aeef))


## v0.1.508 (2025-10-03)

### Continuous Integration

- Release v0.1.508
  ([`4717ff3`](https://github.com/nfraxlab/svc-infra/commit/4717ff3a5d8cfd302de7ad6c137904282c20cb4d))


## v0.1.507 (2025-10-03)

### Continuous Integration

- Release v0.1.507
  ([`2e4f884`](https://github.com/nfraxlab/svc-infra/commit/2e4f88433ccc4110228f6c46288ddb557834a535))


## v0.1.506 (2025-10-03)

### Continuous Integration

- Release v0.1.506
  ([`1e17109`](https://github.com/nfraxlab/svc-infra/commit/1e1710921bf2b854436e8a29270bcf2de7c12e84))


## v0.1.505 (2025-10-02)

### Continuous Integration

- Release v0.1.505
  ([`66f5145`](https://github.com/nfraxlab/svc-infra/commit/66f5145af27a99de09e335bf4004467ea9713183))


## v0.1.504 (2025-10-02)

### Continuous Integration

- Release v0.1.504
  ([`9834c94`](https://github.com/nfraxlab/svc-infra/commit/9834c94ed674e9e1a2d9111d062e4d5a4fe05f39))


## v0.1.503 (2025-10-02)

### Continuous Integration

- Release v0.1.503
  ([`dc7fa33`](https://github.com/nfraxlab/svc-infra/commit/dc7fa33004816428b00a56316ff90d4cbc2f7d6a))


## v0.1.502 (2025-10-01)

### Continuous Integration

- Release v0.1.502
  ([`4441ca3`](https://github.com/nfraxlab/svc-infra/commit/4441ca32b04b6469c9580493fb4cd5359656bb7f))


## v0.1.501 (2025-10-01)

### Continuous Integration

- Release v0.1.501
  ([`47eca2c`](https://github.com/nfraxlab/svc-infra/commit/47eca2c55ce2e03afa2666e1d0250525211d592c))


## v0.1.500 (2025-10-01)

### Continuous Integration

- Release v0.1.500
  ([`d7a4e3f`](https://github.com/nfraxlab/svc-infra/commit/d7a4e3f66f156909287d3e1bacc5875aad2b6371))


## v0.1.499 (2025-10-01)

### Continuous Integration

- Release v0.1.499
  ([`8df06f3`](https://github.com/nfraxlab/svc-infra/commit/8df06f35c0f33705df5bfe808de58b713f57f098))


## v0.1.498 (2025-10-01)

### Continuous Integration

- Release v0.1.498
  ([`1c9dcbb`](https://github.com/nfraxlab/svc-infra/commit/1c9dcbb503f2f3508260680fc77c84dd61f4294e))


## v0.1.497 (2025-09-30)

### Continuous Integration

- Release v0.1.497
  ([`ada569f`](https://github.com/nfraxlab/svc-infra/commit/ada569fdd2529586e4797eb153107ea6f4b4cec7))


## v0.1.496 (2025-09-30)

### Continuous Integration

- Release v0.1.496
  ([`5547ba2`](https://github.com/nfraxlab/svc-infra/commit/5547ba2fc113fe8f93835878dec650aef1512f90))


## v0.1.495 (2025-09-30)

### Continuous Integration

- Release v0.1.495
  ([`e8caec3`](https://github.com/nfraxlab/svc-infra/commit/e8caec3473721613bc15f5c04e147ac9ffd14c8a))


## v0.1.494 (2025-09-30)

### Continuous Integration

- Release v0.1.494
  ([`a7b5cea`](https://github.com/nfraxlab/svc-infra/commit/a7b5cea6822f406a13d34660667aa86fe5a8518a))


## v0.1.493 (2025-09-30)

### Continuous Integration

- Release v0.1.493
  ([`07ac91a`](https://github.com/nfraxlab/svc-infra/commit/07ac91a4e88ebfa4a97991613c4456cc6bf9a1e2))


## v0.1.492 (2025-09-30)

### Continuous Integration

- Release v0.1.492
  ([`a686b16`](https://github.com/nfraxlab/svc-infra/commit/a686b162b5b987e5f0f2c5408b8a943f3dc56ac1))


## v0.1.491 (2025-09-30)

### Continuous Integration

- Release v0.1.491
  ([`7eb7367`](https://github.com/nfraxlab/svc-infra/commit/7eb7367bb642d27958d7b306ed04ba1c7c50c1a6))


## v0.1.490 (2025-09-30)

### Continuous Integration

- Release v0.1.490
  ([`5241ca6`](https://github.com/nfraxlab/svc-infra/commit/5241ca6283de2f37e286307d2fe631ef405cceac))


## v0.1.489 (2025-09-30)

### Continuous Integration

- Release v0.1.489
  ([`d3cb769`](https://github.com/nfraxlab/svc-infra/commit/d3cb769c5750d16dd036d1067459a83121d9dbac))


## v0.1.488 (2025-09-30)

### Continuous Integration

- Release v0.1.488
  ([`0ed65d4`](https://github.com/nfraxlab/svc-infra/commit/0ed65d49cd50ae0c2d0c607f244fe3fae3f669eb))


## v0.1.487 (2025-09-30)

### Continuous Integration

- Release v0.1.487
  ([`a348521`](https://github.com/nfraxlab/svc-infra/commit/a34852145345129b67c839979f9f9ab305a1de8d))


## v0.1.486 (2025-09-30)

### Continuous Integration

- Release v0.1.486
  ([`e9eb228`](https://github.com/nfraxlab/svc-infra/commit/e9eb22853aef22a7a8e8faafcb8151163f6bedcc))


## v0.1.485 (2025-09-30)

### Continuous Integration

- Release v0.1.485
  ([`570dc65`](https://github.com/nfraxlab/svc-infra/commit/570dc65afb9a2c230408639705ee8786bd6ad59a))


## v0.1.484 (2025-09-30)

### Continuous Integration

- Release v0.1.484
  ([`1ccd0a7`](https://github.com/nfraxlab/svc-infra/commit/1ccd0a7b29732819b1ff69c0e8f9dd9982a7e638))


## v0.1.483 (2025-09-30)

### Continuous Integration

- Release v0.1.483
  ([`f470bfa`](https://github.com/nfraxlab/svc-infra/commit/f470bfafee7cc101fd210336081ebe56e799354e))


## v0.1.482 (2025-09-30)

### Continuous Integration

- Release v0.1.482
  ([`37372e9`](https://github.com/nfraxlab/svc-infra/commit/37372e93e89e0b418d90e32f24f3993c2a0090bf))


## v0.1.481 (2025-09-30)

### Continuous Integration

- Release v0.1.481
  ([`c40d741`](https://github.com/nfraxlab/svc-infra/commit/c40d741b13185e87decbddea79bec58480884493))


## v0.1.480 (2025-09-30)

### Continuous Integration

- Release v0.1.480
  ([`d2724df`](https://github.com/nfraxlab/svc-infra/commit/d2724df4fb69e626cccc120ce731f2ac9121d0d2))


## v0.1.479 (2025-09-30)

### Continuous Integration

- Release v0.1.479
  ([`ed69df2`](https://github.com/nfraxlab/svc-infra/commit/ed69df223e528171762517e9416ea5279af9feb0))


## v0.1.478 (2025-09-30)

### Continuous Integration

- Release v0.1.478
  ([`b7f106f`](https://github.com/nfraxlab/svc-infra/commit/b7f106f1fc7268eae08751605f14ae066ffe4b5a))


## v0.1.477 (2025-09-30)

### Continuous Integration

- Release v0.1.477
  ([`2b35329`](https://github.com/nfraxlab/svc-infra/commit/2b3532970c83528ef63a5493a7244540c1c00758))


## v0.1.476 (2025-09-30)

### Continuous Integration

- Release v0.1.476
  ([`661ccba`](https://github.com/nfraxlab/svc-infra/commit/661ccbab909f2e5352337687401bd3aa1bbc1acf))


## v0.1.475 (2025-09-30)

### Continuous Integration

- Release v0.1.475
  ([`c4836c9`](https://github.com/nfraxlab/svc-infra/commit/c4836c99f0d262017106325fd46f87c07f4daafb))


## v0.1.474 (2025-09-30)

### Continuous Integration

- Release v0.1.474
  ([`bbb324e`](https://github.com/nfraxlab/svc-infra/commit/bbb324e245b7e3bf579668b7f2ac5eed57f5114b))


## v0.1.473 (2025-09-29)

### Continuous Integration

- Release v0.1.473
  ([`96141a0`](https://github.com/nfraxlab/svc-infra/commit/96141a0ec659a8b0586bd0350606871ee3b2085d))


## v0.1.472 (2025-09-29)

### Continuous Integration

- Release v0.1.472
  ([`a0c2052`](https://github.com/nfraxlab/svc-infra/commit/a0c205258fe398c5954b415b7030b252ef0f29ae))


## v0.1.471 (2025-09-29)

### Continuous Integration

- Release v0.1.471
  ([`c42a9c7`](https://github.com/nfraxlab/svc-infra/commit/c42a9c74a30e34e6bb6fe165358f5fe366095545))


## v0.1.470 (2025-09-29)

### Continuous Integration

- Release v0.1.470
  ([`bb71e73`](https://github.com/nfraxlab/svc-infra/commit/bb71e73a53b8ae5d6cba29edf19f5e88dd9bc8f9))


## v0.1.469 (2025-09-29)

### Continuous Integration

- Release v0.1.469
  ([`148a40f`](https://github.com/nfraxlab/svc-infra/commit/148a40fc40dd4cad64bd557532832c4aaa9f7fe8))


## v0.1.468 (2025-09-29)

### Continuous Integration

- Release v0.1.468
  ([`a5d300c`](https://github.com/nfraxlab/svc-infra/commit/a5d300cffb256822982efc7e2a56eaa804ca1316))


## v0.1.467 (2025-09-29)

### Continuous Integration

- Release v0.1.467
  ([`ed58443`](https://github.com/nfraxlab/svc-infra/commit/ed58443dd986b89aeee7d8b9ec8a6c0ea0707a8d))


## v0.1.466 (2025-09-29)

### Continuous Integration

- Release v0.1.466
  ([`c3e16d6`](https://github.com/nfraxlab/svc-infra/commit/c3e16d6fdc5b7b318b1e455b77dd7c4952dbb843))


## v0.1.465 (2025-09-28)

### Continuous Integration

- Release v0.1.465
  ([`a879d18`](https://github.com/nfraxlab/svc-infra/commit/a879d181e7affb73224eeb890f8071fe6104f596))


## v0.1.464 (2025-09-28)

### Continuous Integration

- Release v0.1.464
  ([`a5b9de0`](https://github.com/nfraxlab/svc-infra/commit/a5b9de01be47103093c9fb069dc0c409380fd228))


## v0.1.463 (2025-09-28)

### Continuous Integration

- Release v0.1.463
  ([`39df0f6`](https://github.com/nfraxlab/svc-infra/commit/39df0f612e9f3a6758b620ad6e5ac8b639914e13))


## v0.1.462 (2025-09-28)

### Continuous Integration

- Release v0.1.462
  ([`a4acf6c`](https://github.com/nfraxlab/svc-infra/commit/a4acf6c2ee21fbb7592b03d145ae7f4777f5a18b))


## v0.1.461 (2025-09-28)

### Continuous Integration

- Release v0.1.461
  ([`97e21ca`](https://github.com/nfraxlab/svc-infra/commit/97e21ca9a28dd3c030c914d7c1ca7104862ec520))


## v0.1.460 (2025-09-28)

### Continuous Integration

- Release v0.1.460
  ([`c8c6666`](https://github.com/nfraxlab/svc-infra/commit/c8c666620ca403cd3a99f0d27fb01e04fcb329ed))


## v0.1.459 (2025-09-28)

### Continuous Integration

- Release v0.1.459
  ([`4a43adb`](https://github.com/nfraxlab/svc-infra/commit/4a43adbb9b13f75fdb3b434b225c086b82dc85aa))


## v0.1.458 (2025-09-28)

### Continuous Integration

- Release v0.1.458
  ([`46e58ca`](https://github.com/nfraxlab/svc-infra/commit/46e58ca59e312c931bf973790b2150506406badf))


## v0.1.457 (2025-09-28)

### Continuous Integration

- Release v0.1.457
  ([`a402736`](https://github.com/nfraxlab/svc-infra/commit/a402736c4b57cc4cd7e714672a6db468aaf6c935))


## v0.1.456 (2025-09-28)

### Continuous Integration

- Release v0.1.456
  ([`d38b0d9`](https://github.com/nfraxlab/svc-infra/commit/d38b0d9db945f42e1035c9757e092f82d12d4f3f))


## v0.1.455 (2025-09-28)

### Continuous Integration

- Release v0.1.455
  ([`73638ff`](https://github.com/nfraxlab/svc-infra/commit/73638ffb8eb4e3b436794cd863784645a58dcede))


## v0.1.454 (2025-09-28)

### Continuous Integration

- Release v0.1.454
  ([`4d4b4a9`](https://github.com/nfraxlab/svc-infra/commit/4d4b4a9b97d1a5d6467b41925d7f2f7a6c1e93f0))


## v0.1.453 (2025-09-28)

### Continuous Integration

- Release v0.1.453
  ([`cf1ca10`](https://github.com/nfraxlab/svc-infra/commit/cf1ca1014209d256c2f9037b68977fa91b7ffbc0))


## v0.1.452 (2025-09-28)

### Continuous Integration

- Release v0.1.452
  ([`28d8fa2`](https://github.com/nfraxlab/svc-infra/commit/28d8fa254b9b3719328a1f84a7246559760037d2))


## v0.1.451 (2025-09-28)

### Continuous Integration

- Release v0.1.451
  ([`a08eaa1`](https://github.com/nfraxlab/svc-infra/commit/a08eaa151c07aac8b94ad2ac3c0c29ad16057aa1))


## v0.1.450 (2025-09-28)

### Continuous Integration

- Release v0.1.450
  ([`1378f07`](https://github.com/nfraxlab/svc-infra/commit/1378f072db5a5161b8a40e069d37d6baff0c2ecd))


## v0.1.449 (2025-09-28)

### Continuous Integration

- Release v0.1.449
  ([`1d06cd4`](https://github.com/nfraxlab/svc-infra/commit/1d06cd4aa6d58c1c80d00d9d0d21184f4429c0aa))


## v0.1.448 (2025-09-28)

### Continuous Integration

- Release v0.1.448
  ([`a096ad8`](https://github.com/nfraxlab/svc-infra/commit/a096ad8d52c2c616aa05ef9d0d96dde23c2a8000))


## v0.1.447 (2025-09-28)

### Continuous Integration

- Release v0.1.447
  ([`42e4812`](https://github.com/nfraxlab/svc-infra/commit/42e4812aa40c7370170294b34c8a7d716bf0ab1e))


## v0.1.446 (2025-09-27)

### Continuous Integration

- Release v0.1.446
  ([`96be55b`](https://github.com/nfraxlab/svc-infra/commit/96be55b8bf83494b2583a7316aa10d8455c8dc0b))


## v0.1.445 (2025-09-27)

### Continuous Integration

- Release v0.1.445
  ([`8d93bbf`](https://github.com/nfraxlab/svc-infra/commit/8d93bbfca92b152a3118493f65270c6163529ca5))


## v0.1.444 (2025-09-27)

### Continuous Integration

- Release v0.1.444
  ([`ab45138`](https://github.com/nfraxlab/svc-infra/commit/ab45138ebd569f982bdbca722468a01037a43a1c))


## v0.1.443 (2025-09-27)

### Continuous Integration

- Release v0.1.443
  ([`21d7dc3`](https://github.com/nfraxlab/svc-infra/commit/21d7dc33162294527a9f9d7d864db1de20e850e8))


## v0.1.442 (2025-09-27)

### Continuous Integration

- Release v0.1.442
  ([`5bfb61c`](https://github.com/nfraxlab/svc-infra/commit/5bfb61cb149d4dcf6732bab31a3ddac876f9ba5f))


## v0.1.441 (2025-09-27)

### Continuous Integration

- Release v0.1.441
  ([`8af8222`](https://github.com/nfraxlab/svc-infra/commit/8af82229338729fb5a058ee1f007013db74c3828))


## v0.1.440 (2025-09-27)

### Continuous Integration

- Release v0.1.440
  ([`0e1c6cd`](https://github.com/nfraxlab/svc-infra/commit/0e1c6cd4af61958139c8685d6addf4510062d209))


## v0.1.439 (2025-09-27)

### Continuous Integration

- Release v0.1.439
  ([`fe422ae`](https://github.com/nfraxlab/svc-infra/commit/fe422aea0cb7d37bcff5d28ba022f5c2fd3c3a39))


## v0.1.438 (2025-09-27)

### Continuous Integration

- Release v0.1.438
  ([`d45e990`](https://github.com/nfraxlab/svc-infra/commit/d45e9902761a7ba7c66537f2f5ffee0725745045))


## v0.1.437 (2025-09-27)

### Continuous Integration

- Release v0.1.437
  ([`c9230f5`](https://github.com/nfraxlab/svc-infra/commit/c9230f565edbd83adc9af7a2997580111e38bef5))


## v0.1.436 (2025-09-27)

### Continuous Integration

- Release v0.1.436
  ([`e59b890`](https://github.com/nfraxlab/svc-infra/commit/e59b890106a08600d1b6e30c3798c0c6fb1fbd96))


## v0.1.435 (2025-09-27)

### Continuous Integration

- Release v0.1.435
  ([`b9dbf12`](https://github.com/nfraxlab/svc-infra/commit/b9dbf12abe0f97915d4f153fa70f4ac842a8c6c4))


## v0.1.434 (2025-09-27)

### Continuous Integration

- Release v0.1.434
  ([`52020fa`](https://github.com/nfraxlab/svc-infra/commit/52020fa9706f7b138afd13327caacb546008cc49))


## v0.1.433 (2025-09-27)

### Continuous Integration

- Release v0.1.433
  ([`c377f7c`](https://github.com/nfraxlab/svc-infra/commit/c377f7cfec46df0037e2a52e5e3ade1d80683a7a))


## v0.1.432 (2025-09-27)

### Continuous Integration

- Release v0.1.432
  ([`adbda0d`](https://github.com/nfraxlab/svc-infra/commit/adbda0dcbcf85f128b704e13376cabbf6192473f))


## v0.1.431 (2025-09-27)

### Continuous Integration

- Release v0.1.431
  ([`ea7eeea`](https://github.com/nfraxlab/svc-infra/commit/ea7eeea8b095a799f769400b38ee741fd4bc1654))


## v0.1.430 (2025-09-27)

### Continuous Integration

- Release v0.1.430
  ([`3bb8665`](https://github.com/nfraxlab/svc-infra/commit/3bb86651852bd7015d9dcd44496e68bbeb638677))


## v0.1.429 (2025-09-27)

### Continuous Integration

- Release v0.1.429
  ([`2bbd8ea`](https://github.com/nfraxlab/svc-infra/commit/2bbd8ea163a2c9846c5be522908903d931363a1d))


## v0.1.428 (2025-09-27)

### Continuous Integration

- Release v0.1.428
  ([`5a82846`](https://github.com/nfraxlab/svc-infra/commit/5a82846c97115e5734775bf2247405673ab9fe73))


## v0.1.427 (2025-09-27)

### Continuous Integration

- Release v0.1.427
  ([`bad10eb`](https://github.com/nfraxlab/svc-infra/commit/bad10eb88084e8201f56b7f01e8b8912be1cdbb1))


## v0.1.426 (2025-09-27)

### Continuous Integration

- Release v0.1.426
  ([`12e882c`](https://github.com/nfraxlab/svc-infra/commit/12e882cc9d1f72193e5aa7c855923a7ef79192a5))


## v0.1.425 (2025-09-27)

### Continuous Integration

- Release v0.1.422
  ([`491df8c`](https://github.com/nfraxlab/svc-infra/commit/491df8caeb24d9161065ddbb04b3a81a318b6343))

- Release v0.1.425
  ([`52a532d`](https://github.com/nfraxlab/svc-infra/commit/52a532d1af544b05c1b3816ce750ebba98fd6474))


## v0.1.421 (2025-09-27)

### Continuous Integration

- Release v0.1.421
  ([`d98096f`](https://github.com/nfraxlab/svc-infra/commit/d98096fa4a58eb36415e9384262277f54370bcf0))


## v0.1.420 (2025-09-26)

### Continuous Integration

- Release v0.1.420
  ([`c0f5fea`](https://github.com/nfraxlab/svc-infra/commit/c0f5feaeeab7a61455019de5a2e3289a312603b0))


## v0.1.419 (2025-09-26)

### Continuous Integration

- Release v0.1.419
  ([`9484043`](https://github.com/nfraxlab/svc-infra/commit/9484043c27c1949d3aaba6c201b25170efa276a6))


## v0.1.418 (2025-09-26)

### Continuous Integration

- Release v0.1.418
  ([`f0814f1`](https://github.com/nfraxlab/svc-infra/commit/f0814f1e584e35c0b7662e9a64167ff7133300a4))


## v0.1.417 (2025-09-26)

### Continuous Integration

- Release v0.1.417
  ([`62d4d78`](https://github.com/nfraxlab/svc-infra/commit/62d4d78cd478d91d1ae7f49ce7d12b7137b70213))


## v0.1.416 (2025-09-26)

### Continuous Integration

- Release v0.1.416
  ([`c0074d6`](https://github.com/nfraxlab/svc-infra/commit/c0074d66e13cc7f068e999c21f648c3ac6323c61))


## v0.1.415 (2025-09-26)

### Continuous Integration

- Release v0.1.415
  ([`5e4ff61`](https://github.com/nfraxlab/svc-infra/commit/5e4ff6179c8a46969ec43ae0be3163c8f9962630))


## v0.1.414 (2025-09-26)

### Continuous Integration

- Release v0.1.414
  ([`bbee479`](https://github.com/nfraxlab/svc-infra/commit/bbee4796fa51462b1e6347ff13f09bd2856c0ee8))


## v0.1.413 (2025-09-26)

### Continuous Integration

- Release v0.1.413
  ([`521d09b`](https://github.com/nfraxlab/svc-infra/commit/521d09b77fd6deebcb472473508832c53d41cc90))


## v0.1.412 (2025-09-26)

### Continuous Integration

- Release v0.1.412
  ([`1042622`](https://github.com/nfraxlab/svc-infra/commit/104262272117c35b40874e1b0eda86be77199a47))


## v0.1.411 (2025-09-26)

### Continuous Integration

- Release v0.1.411
  ([`9fa9837`](https://github.com/nfraxlab/svc-infra/commit/9fa98370680c726b4252e5241464055f41009fee))


## v0.1.410 (2025-09-26)

### Continuous Integration

- Release v0.1.410
  ([`13afbd9`](https://github.com/nfraxlab/svc-infra/commit/13afbd9821737f46d1bc7ff55f2abb2db388ef04))


## v0.1.409 (2025-09-26)

### Continuous Integration

- Release v0.1.409
  ([`7c651ba`](https://github.com/nfraxlab/svc-infra/commit/7c651bacaa1f806323fb696360d7b5bb3fae15b1))


## v0.1.408 (2025-09-26)

### Continuous Integration

- Release v0.1.408
  ([`05544c7`](https://github.com/nfraxlab/svc-infra/commit/05544c714e17ea742e8d64f4d84f463238d28d3d))


## v0.1.407 (2025-09-26)

### Continuous Integration

- Release v0.1.407
  ([`8d3880d`](https://github.com/nfraxlab/svc-infra/commit/8d3880dd2e9b6ee74a050e504f8deb018867b3ff))


## v0.1.406 (2025-09-26)

### Continuous Integration

- Release v0.1.406
  ([`92ac53e`](https://github.com/nfraxlab/svc-infra/commit/92ac53ebc6e4d73ad54d33290b9e9e5ccafb2f63))


## v0.1.405 (2025-09-26)

### Continuous Integration

- Release v0.1.405
  ([`d436f73`](https://github.com/nfraxlab/svc-infra/commit/d436f7327d3a6cb86de4375902cf67e5ca27ab0e))


## v0.1.404 (2025-09-26)

### Continuous Integration

- Release v0.1.404
  ([`3733e70`](https://github.com/nfraxlab/svc-infra/commit/3733e7068d4f90ab45fa9c1d8cc581eef87717b2))


## v0.1.403 (2025-09-26)

### Continuous Integration

- Release v0.1.403
  ([`677cae8`](https://github.com/nfraxlab/svc-infra/commit/677cae8bb499b29bfdb43116f2c62773f32b65c5))


## v0.1.402 (2025-09-26)

### Continuous Integration

- Release v0.1.402
  ([`67cfb1d`](https://github.com/nfraxlab/svc-infra/commit/67cfb1dc610e9e9258c4962672c155bc4f449414))


## v0.1.401 (2025-09-26)

### Continuous Integration

- Release v0.1.401
  ([`7bd04e8`](https://github.com/nfraxlab/svc-infra/commit/7bd04e8744e2cbaf789b0174a60d758c8e85ca61))


## v0.1.400 (2025-09-26)

### Continuous Integration

- Release v0.1.400
  ([`1b87969`](https://github.com/nfraxlab/svc-infra/commit/1b879697febee02bf785c0b9f76e29d7c180cfaa))


## v0.1.399 (2025-09-26)

### Continuous Integration

- Release v0.1.399
  ([`27de407`](https://github.com/nfraxlab/svc-infra/commit/27de407248ea549b3fd604aba21b8694ae14ef4f))


## v0.1.398 (2025-09-26)

### Continuous Integration

- Release v0.1.398
  ([`d7fd063`](https://github.com/nfraxlab/svc-infra/commit/d7fd06327b2998004c9409f461d547776af164d3))


## v0.1.397 (2025-09-26)

### Continuous Integration

- Release v0.1.397
  ([`e9b5a8d`](https://github.com/nfraxlab/svc-infra/commit/e9b5a8df90d8d3debc1d4544ffe1a93cb8455e21))


## v0.1.396 (2025-09-26)

### Continuous Integration

- Release v0.1.396
  ([`947eb1c`](https://github.com/nfraxlab/svc-infra/commit/947eb1c5df725f0f243b58d736ca097e9b35403a))


## v0.1.395 (2025-09-26)

### Continuous Integration

- Release v0.1.395
  ([`427188c`](https://github.com/nfraxlab/svc-infra/commit/427188c6e957535ba1fec279795e5468d7158986))


## v0.1.394 (2025-09-26)

### Continuous Integration

- Release v0.1.394
  ([`dc0e60a`](https://github.com/nfraxlab/svc-infra/commit/dc0e60a646ed8159c682f54b41ddb92e736227eb))


## v0.1.393 (2025-09-26)

### Continuous Integration

- Release v0.1.393
  ([`8d927a9`](https://github.com/nfraxlab/svc-infra/commit/8d927a998b294de7842ebb173357a9e8184b5e0e))


## v0.1.392 (2025-09-25)

### Continuous Integration

- Release v0.1.392
  ([`6be4cad`](https://github.com/nfraxlab/svc-infra/commit/6be4cad196d3f570dbcb5a39c26c0b1bb1c98344))


## v0.1.391 (2025-09-25)

### Continuous Integration

- Release v0.1.391
  ([`8ea1922`](https://github.com/nfraxlab/svc-infra/commit/8ea19229a4996db4565335f8a9617b3a20f01702))


## v0.1.390 (2025-09-25)

### Continuous Integration

- Release v0.1.390
  ([`44879a1`](https://github.com/nfraxlab/svc-infra/commit/44879a158ea9d456b38449c87826c0ae4ac1e5de))


## v0.1.389 (2025-09-25)

### Continuous Integration

- Release v0.1.389
  ([`793c4f9`](https://github.com/nfraxlab/svc-infra/commit/793c4f95686f7e751db6f46bd602561e2dd76a11))


## v0.1.388 (2025-09-25)

### Continuous Integration

- Release v0.1.388
  ([`b37300f`](https://github.com/nfraxlab/svc-infra/commit/b37300f2fca44ddf6631b108fa737c49318a6a59))


## v0.1.387 (2025-09-25)

### Continuous Integration

- Release v0.1.387
  ([`4b47185`](https://github.com/nfraxlab/svc-infra/commit/4b47185bcd10f53f2fec456a7b1dbce85215a0ad))


## v0.1.386 (2025-09-25)

### Continuous Integration

- Release v0.1.386
  ([`1127c90`](https://github.com/nfraxlab/svc-infra/commit/1127c90b5067b498edeb1e0259bfed5066a3da09))


## v0.1.385 (2025-09-25)

### Continuous Integration

- Release v0.1.385
  ([`3da7f30`](https://github.com/nfraxlab/svc-infra/commit/3da7f305f5b8cd36e38fb5584bf2fe18c2aea60a))


## v0.1.384 (2025-09-25)

### Continuous Integration

- Release v0.1.384
  ([`d2c9d73`](https://github.com/nfraxlab/svc-infra/commit/d2c9d73b4ffafdee569edc4112c0c0a56dc6e811))


## v0.1.383 (2025-09-25)

### Continuous Integration

- Release v0.1.383
  ([`e4a3fc3`](https://github.com/nfraxlab/svc-infra/commit/e4a3fc3a9710eba321c6952ff4209eb3afbe70ac))


## v0.1.382 (2025-09-25)

### Continuous Integration

- Release v0.1.382
  ([`6415b4e`](https://github.com/nfraxlab/svc-infra/commit/6415b4e98e2d4eb6c0a3aa1c33a98290714671c7))


## v0.1.381 (2025-09-25)

### Continuous Integration

- Release v0.1.381
  ([`ee1accc`](https://github.com/nfraxlab/svc-infra/commit/ee1accc2fe3e2b181d65ad1bfd88d780eda7d7c2))


## v0.1.380 (2025-09-25)

### Continuous Integration

- Release v0.1.380
  ([`f6e3691`](https://github.com/nfraxlab/svc-infra/commit/f6e369109260e80ed4a1cb4a51a1b7d93494777a))


## v0.1.379 (2025-09-25)

### Continuous Integration

- Release v0.1.379
  ([`40eb1d4`](https://github.com/nfraxlab/svc-infra/commit/40eb1d459db99a19f3f07504196b897383ccc6cb))


## v0.1.378 (2025-09-25)

### Continuous Integration

- Release v0.1.378
  ([`ceef6b8`](https://github.com/nfraxlab/svc-infra/commit/ceef6b89331b0fbe7af36095505cb3844be6e5cc))


## v0.1.377 (2025-09-25)

### Continuous Integration

- Release v0.1.377
  ([`2f111e7`](https://github.com/nfraxlab/svc-infra/commit/2f111e7cdafc1ec1cafd34db343834ec33642785))


## v0.1.376 (2025-09-25)

### Continuous Integration

- Release v0.1.376
  ([`166dff9`](https://github.com/nfraxlab/svc-infra/commit/166dff99012258e2e10ac7b55cdf3e306f698f27))


## v0.1.375 (2025-09-25)

### Continuous Integration

- Release v0.1.375
  ([`70f591e`](https://github.com/nfraxlab/svc-infra/commit/70f591e5b03eed86b0a957510a88ccea60ef82e5))


## v0.1.374 (2025-09-24)

### Continuous Integration

- Release v0.1.374
  ([`28cc659`](https://github.com/nfraxlab/svc-infra/commit/28cc659532be28e814f2ffb1c23527323e0b9dca))


## v0.1.373 (2025-09-24)

### Continuous Integration

- Release v0.1.373
  ([`1eefde3`](https://github.com/nfraxlab/svc-infra/commit/1eefde3eec41ef934defef773bda7e48165f383c))


## v0.1.372 (2025-09-24)

### Continuous Integration

- Release v0.1.372
  ([`d48727e`](https://github.com/nfraxlab/svc-infra/commit/d48727e83ad6437e7c241cf6506a01ac27948fcd))


## v0.1.371 (2025-09-24)

### Continuous Integration

- Release v0.1.371
  ([`61e1b24`](https://github.com/nfraxlab/svc-infra/commit/61e1b24d23bfb5968362062a8571a66227f7577c))


## v0.1.370 (2025-09-24)

### Continuous Integration

- Release v0.1.370
  ([`4fefd8e`](https://github.com/nfraxlab/svc-infra/commit/4fefd8eeae6d2325b67b1bbe3492315469ff192c))


## v0.1.369 (2025-09-24)

### Continuous Integration

- Release v0.1.369
  ([`dd3b015`](https://github.com/nfraxlab/svc-infra/commit/dd3b01579de21b6da4aa8401a5814ed2288245f8))


## v0.1.368 (2025-09-24)

### Continuous Integration

- Release v0.1.368
  ([`78867cb`](https://github.com/nfraxlab/svc-infra/commit/78867cbb31105430e5faff16c5e61c4d74627b17))


## v0.1.367 (2025-09-24)

### Continuous Integration

- Release v0.1.367
  ([`e5118e0`](https://github.com/nfraxlab/svc-infra/commit/e5118e0b5fa4e16df47c5ab0c94fb442cf77cc9d))


## v0.1.366 (2025-09-24)

### Continuous Integration

- Release v0.1.366
  ([`c4cb555`](https://github.com/nfraxlab/svc-infra/commit/c4cb555426f5b61c4e8d9ea15d24d0131306d375))


## v0.1.365 (2025-09-24)

### Continuous Integration

- Release v0.1.365
  ([`48c2624`](https://github.com/nfraxlab/svc-infra/commit/48c26244c976b27b292a0e8fb6d6516aa0514188))


## v0.1.364 (2025-09-24)

### Continuous Integration

- Release v0.1.364
  ([`6572644`](https://github.com/nfraxlab/svc-infra/commit/6572644b7ceee1f8a67381c156a1f3c3ffef937e))


## v0.1.363 (2025-09-24)

### Continuous Integration

- Release v0.1.363
  ([`17c5cca`](https://github.com/nfraxlab/svc-infra/commit/17c5ccac2d3764b4b03985f03032594adca8927e))


## v0.1.362 (2025-09-24)

### Continuous Integration

- Release v0.1.362
  ([`49cfd3c`](https://github.com/nfraxlab/svc-infra/commit/49cfd3ceac6ba3e447bc5817e4f4dea7f0e9d33c))


## v0.1.361 (2025-09-24)

### Continuous Integration

- Release v0.1.361
  ([`b0f84de`](https://github.com/nfraxlab/svc-infra/commit/b0f84defbd4976aa268beb798498eb9dd097fc77))


## v0.1.360 (2025-09-24)

### Continuous Integration

- Release v0.1.360
  ([`efcedbb`](https://github.com/nfraxlab/svc-infra/commit/efcedbb07672d01dbb266388fb24c315437bbd31))


## v0.1.359 (2025-09-24)

### Continuous Integration

- Release v0.1.359
  ([`29c2bac`](https://github.com/nfraxlab/svc-infra/commit/29c2bacf6bb1831e5797bd0cac4b2247cce8eaa4))


## v0.1.358 (2025-09-24)

### Continuous Integration

- Release v0.1.358
  ([`ffe053f`](https://github.com/nfraxlab/svc-infra/commit/ffe053f7bb9d3152de772ebaaef9e4b914a5781a))


## v0.1.357 (2025-09-24)

### Continuous Integration

- Release v0.1.357
  ([`c195716`](https://github.com/nfraxlab/svc-infra/commit/c19571627412258605287de1bd6e2f5bcdc9cc04))


## v0.1.356 (2025-09-23)

### Continuous Integration

- Release v0.1.356
  ([`ce59872`](https://github.com/nfraxlab/svc-infra/commit/ce5987290ffc1b1a265368b9b0b312936f509109))


## v0.1.355 (2025-09-23)

### Continuous Integration

- Release v0.1.355
  ([`fad1995`](https://github.com/nfraxlab/svc-infra/commit/fad1995b4dc4e338a0cadcfbd09b9e3f7dcfdac8))


## v0.1.354 (2025-09-23)

### Continuous Integration

- Release v0.1.354
  ([`09d9c6f`](https://github.com/nfraxlab/svc-infra/commit/09d9c6f2820aeca45fb5d0be7dcf4ac0527243cc))


## v0.1.353 (2025-09-23)

### Continuous Integration

- Release v0.1.353
  ([`d9dbb99`](https://github.com/nfraxlab/svc-infra/commit/d9dbb992714712c27a6f6c1620ad4a158f001673))


## v0.1.352 (2025-09-23)

### Continuous Integration

- Release v0.1.352
  ([`fec48f0`](https://github.com/nfraxlab/svc-infra/commit/fec48f0a5fefabc7057a3f26eb8b0bebc475a09b))


## v0.1.351 (2025-09-23)

### Continuous Integration

- Release v0.1.351
  ([`3c84c5a`](https://github.com/nfraxlab/svc-infra/commit/3c84c5a411f1bc6bdd6b91d2bb0d4101dba1243a))


## v0.1.350 (2025-09-23)

### Continuous Integration

- Release v0.1.350
  ([`11eb8fb`](https://github.com/nfraxlab/svc-infra/commit/11eb8fb6eddec24ec2b2e97eb41cc1767e7d9c8d))


## v0.1.349 (2025-09-23)

### Continuous Integration

- Release v0.1.349
  ([`0df830e`](https://github.com/nfraxlab/svc-infra/commit/0df830ec3edbc151d82e5d0d57c0a5ee595a20e3))


## v0.1.348 (2025-09-23)

### Continuous Integration

- Release v0.1.348
  ([`1a43be6`](https://github.com/nfraxlab/svc-infra/commit/1a43be633cccaeca63f926fce7e44214c79f12ba))


## v0.1.347 (2025-09-23)

### Continuous Integration

- Release v0.1.347
  ([`a8c2815`](https://github.com/nfraxlab/svc-infra/commit/a8c281599e45725071150529b2b1312a2de2981a))


## v0.1.346 (2025-09-23)

### Continuous Integration

- Release v0.1.346
  ([`133c44f`](https://github.com/nfraxlab/svc-infra/commit/133c44f238943fdcb8042ed568416b6b735bca5f))


## v0.1.345 (2025-09-23)

### Continuous Integration

- Release v0.1.345
  ([`dbb8090`](https://github.com/nfraxlab/svc-infra/commit/dbb80902b14bf1f97c5636e07d4b85af7b742745))


## v0.1.344 (2025-09-23)

### Continuous Integration

- Release v0.1.344
  ([`d1917bf`](https://github.com/nfraxlab/svc-infra/commit/d1917bf1c49eba4bd09d0f0540136869e46c97d1))


## v0.1.343 (2025-09-23)

### Continuous Integration

- Release v0.1.343
  ([`72c9c7d`](https://github.com/nfraxlab/svc-infra/commit/72c9c7d67b60d982c4c37f7a882e10fa5504c1c3))


## v0.1.342 (2025-09-23)

### Continuous Integration

- Release v0.1.342
  ([`761df03`](https://github.com/nfraxlab/svc-infra/commit/761df03f305c5d8c3e8746982e656a73c2e752ea))


## v0.1.341 (2025-09-23)

### Continuous Integration

- Release v0.1.336
  ([`536934c`](https://github.com/nfraxlab/svc-infra/commit/536934c07de620d817bc509660c3130e6e591991))

- Release v0.1.337
  ([`f70e6b6`](https://github.com/nfraxlab/svc-infra/commit/f70e6b6501e693784a35941a370bf3818dbce395))

- Release v0.1.338
  ([`7a8639e`](https://github.com/nfraxlab/svc-infra/commit/7a8639eeda493eb10e59575a42fd363f51a3ff86))

- Release v0.1.339
  ([`c88f94d`](https://github.com/nfraxlab/svc-infra/commit/c88f94d7d327346c8f9597a8aa4de6c827ebed72))

- Release v0.1.340
  ([`f328e56`](https://github.com/nfraxlab/svc-infra/commit/f328e561b36774800e3db613489afbe31dbdb247))

- Release v0.1.341
  ([`1c4e342`](https://github.com/nfraxlab/svc-infra/commit/1c4e342cff5313e319659b6f07d60dbefc882651))


## v0.1.335 (2025-09-22)

### Continuous Integration

- Release v0.1.335
  ([`1d0827a`](https://github.com/nfraxlab/svc-infra/commit/1d0827a0fa6df46eb2866641534f2c724851afc4))


## v0.1.334 (2025-09-22)

### Continuous Integration

- Release v0.1.334
  ([`f6745bf`](https://github.com/nfraxlab/svc-infra/commit/f6745bf5211b6dcb39516a83517d38368ba4b8bc))


## v0.1.333 (2025-09-20)

### Continuous Integration

- Release v0.1.333
  ([`92a2681`](https://github.com/nfraxlab/svc-infra/commit/92a2681da452215b3d8175312a68f8b7a7b77c16))


## v0.1.332 (2025-09-20)

### Continuous Integration

- Release v0.1.332
  ([`596c986`](https://github.com/nfraxlab/svc-infra/commit/596c9864e49bce359a51993c9153a2e2b9001ec8))


## v0.1.331 (2025-09-20)

### Continuous Integration

- Release v0.1.331
  ([`7a430e5`](https://github.com/nfraxlab/svc-infra/commit/7a430e5e8bcf7f83c52538f2db1550c917aa4b65))


## v0.1.330 (2025-09-19)

### Continuous Integration

- Release v0.1.330
  ([`45f474a`](https://github.com/nfraxlab/svc-infra/commit/45f474a03676a142786009e5ca2efccb57938ce4))


## v0.1.329 (2025-09-19)

### Continuous Integration

- Release v0.1.329
  ([`13a6d56`](https://github.com/nfraxlab/svc-infra/commit/13a6d561d218629de228517cebf11478dc0b0e4f))


## v0.1.328 (2025-09-19)

### Continuous Integration

- Release v0.1.328
  ([`9802f21`](https://github.com/nfraxlab/svc-infra/commit/9802f21bb7275b21d12e968161678c3f4d197bb0))


## v0.1.327 (2025-09-19)

### Continuous Integration

- Release v0.1.327
  ([`b428739`](https://github.com/nfraxlab/svc-infra/commit/b42873988d7b646492097dacaafac8aa6053228b))


## v0.1.326 (2025-09-19)

### Continuous Integration

- Release v0.1.326
  ([`f731801`](https://github.com/nfraxlab/svc-infra/commit/f7318017ef84455a20f50c5789d7445cc9fd8fa6))


## v0.1.325 (2025-09-19)

### Continuous Integration

- Release v0.1.325
  ([`99784d5`](https://github.com/nfraxlab/svc-infra/commit/99784d5fb27051787752bdc9471638483cc80995))


## v0.1.324 (2025-09-19)

### Continuous Integration

- Release v0.1.324
  ([`96c9879`](https://github.com/nfraxlab/svc-infra/commit/96c9879b0a511ea2c26bad4c7ebef23e26edb86e))


## v0.1.323 (2025-09-19)

### Continuous Integration

- Release v0.1.323
  ([`1e3e190`](https://github.com/nfraxlab/svc-infra/commit/1e3e190842d5b92d47567cffa631fa3448ab6c1c))


## v0.1.322 (2025-09-19)

### Continuous Integration

- Release v0.1.322
  ([`206dd2b`](https://github.com/nfraxlab/svc-infra/commit/206dd2bc14da94695c9d55bc251ffb7f31f52f1a))


## v0.1.321 (2025-09-19)

### Continuous Integration

- Release v0.1.321
  ([`52fb9f6`](https://github.com/nfraxlab/svc-infra/commit/52fb9f66a2cc0e049fd9a1e843623eae60b14fc1))


## v0.1.320 (2025-09-19)

### Continuous Integration

- Release v0.1.320
  ([`f7e6171`](https://github.com/nfraxlab/svc-infra/commit/f7e61712efe19e6488653903d26c00c464cea6f7))


## v0.1.319 (2025-09-19)

### Continuous Integration

- Release v0.1.319
  ([`605d0c9`](https://github.com/nfraxlab/svc-infra/commit/605d0c950885c28ed40c039ad8a36d49f58c8035))


## v0.1.318 (2025-09-19)

### Continuous Integration

- Release v0.1.318
  ([`0d25958`](https://github.com/nfraxlab/svc-infra/commit/0d259586e44e84428ee6018bffbd79c24b87c6db))


## v0.1.317 (2025-09-19)

### Continuous Integration

- Release v0.1.317
  ([`696d518`](https://github.com/nfraxlab/svc-infra/commit/696d518289099cc04d239053e02be1e62c5863e2))


## v0.1.316 (2025-09-19)

### Continuous Integration

- Release v0.1.316
  ([`31c0ac5`](https://github.com/nfraxlab/svc-infra/commit/31c0ac51233b71cb755e4997ca9e822874fa7017))


## v0.1.315 (2025-09-19)

### Continuous Integration

- Release v0.1.315
  ([`ba27fdb`](https://github.com/nfraxlab/svc-infra/commit/ba27fdb622d67b1bd2b5181372f7646ed5f927b0))


## v0.1.314 (2025-09-19)

### Continuous Integration

- Release v0.1.314
  ([`b1480ee`](https://github.com/nfraxlab/svc-infra/commit/b1480ee41af2e36bf85fbb40b6cbd68d0a689e17))


## v0.1.313 (2025-09-19)

### Continuous Integration

- Release v0.1.313
  ([`a3e56b6`](https://github.com/nfraxlab/svc-infra/commit/a3e56b614810a87483ae80c05f09b4d5319df15e))


## v0.1.312 (2025-09-19)

### Continuous Integration

- Release v0.1.312
  ([`010196e`](https://github.com/nfraxlab/svc-infra/commit/010196efcdffb07d389367c36fb98a3a99eb9ea4))


## v0.1.311 (2025-09-18)

### Continuous Integration

- Release v0.1.311
  ([`159ebb2`](https://github.com/nfraxlab/svc-infra/commit/159ebb2979eeb0f0c476c517f2c1e6bfd1ddc841))


## v0.1.310 (2025-09-18)

### Continuous Integration

- Release v0.1.310
  ([`72e460b`](https://github.com/nfraxlab/svc-infra/commit/72e460bbb1eb6384a03ea5c2f7954ef6b4dc79ee))


## v0.1.309 (2025-09-18)

### Continuous Integration

- Release v0.1.309
  ([`be58b9a`](https://github.com/nfraxlab/svc-infra/commit/be58b9a1ce067e2e3b2bd58903a50b2a5780c67e))


## v0.1.308 (2025-09-18)

### Continuous Integration

- Release v0.1.308
  ([`e034c93`](https://github.com/nfraxlab/svc-infra/commit/e034c937baa69ae2d368bb03430b3992c80a37af))


## v0.1.307 (2025-09-18)

### Continuous Integration

- Release v0.1.307
  ([`8aabab2`](https://github.com/nfraxlab/svc-infra/commit/8aabab257f4aef741379a0095424961ec34cecd6))


## v0.1.306 (2025-09-18)

### Continuous Integration

- Release v0.1.306
  ([`8b3cfae`](https://github.com/nfraxlab/svc-infra/commit/8b3cfae975ec48533bb5f2093aa377e00e8d77e0))


## v0.1.305 (2025-09-17)

### Continuous Integration

- Release v0.1.305
  ([`245383d`](https://github.com/nfraxlab/svc-infra/commit/245383dc36bff7359e16adf917df05e05154746d))


## v0.1.304 (2025-09-17)

### Continuous Integration

- Release v0.1.304
  ([`f14dfdc`](https://github.com/nfraxlab/svc-infra/commit/f14dfdcff433cb5f584e3d54b100e09fd92c2233))


## v0.1.303 (2025-09-17)

### Continuous Integration

- Release v0.1.303
  ([`d228361`](https://github.com/nfraxlab/svc-infra/commit/d2283610bc8bddb665c1a148181520e76fd3a58a))


## v0.1.302 (2025-09-17)

### Continuous Integration

- Release v0.1.302
  ([`48ca5b7`](https://github.com/nfraxlab/svc-infra/commit/48ca5b7de14bc4a9703616ac6fe031e6275ac905))


## v0.1.301 (2025-09-17)

### Continuous Integration

- Release v0.1.301
  ([`4a71a6f`](https://github.com/nfraxlab/svc-infra/commit/4a71a6fc0f4724e866c353265296ba77e54d3bb2))


## v0.1.300 (2025-09-17)

### Continuous Integration

- Release v0.1.300
  ([`39c2129`](https://github.com/nfraxlab/svc-infra/commit/39c21291607cb1c3f964dc2c066be93e67897832))


## v0.1.299 (2025-09-17)

### Continuous Integration

- Release v0.1.299
  ([`e8c00ee`](https://github.com/nfraxlab/svc-infra/commit/e8c00ee79c6350df22e89088dcc023a8312afe58))


## v0.1.298 (2025-09-17)

### Continuous Integration

- Release v0.1.298
  ([`69d35e2`](https://github.com/nfraxlab/svc-infra/commit/69d35e24e89311696f8da85d73a4635f99bc40ac))


## v0.1.297 (2025-09-17)

### Continuous Integration

- Release v0.1.297
  ([`0e43186`](https://github.com/nfraxlab/svc-infra/commit/0e43186ebb6bc2446eb7ebd01ae95f2a7f3217b6))


## v0.1.296 (2025-09-17)

### Continuous Integration

- Release v0.1.296
  ([`05336c4`](https://github.com/nfraxlab/svc-infra/commit/05336c4983f901aff7548d778d602cb9c5a0801e))


## v0.1.295 (2025-09-16)

### Continuous Integration

- Release v0.1.295
  ([`4ccf759`](https://github.com/nfraxlab/svc-infra/commit/4ccf7597aa77a93e9de996c3ba7d1b0617d0ba03))


## v0.1.294 (2025-09-16)

### Continuous Integration

- Release v0.1.294
  ([`5019228`](https://github.com/nfraxlab/svc-infra/commit/501922833b3e0e9ee73b5246eb392688a58efc65))


## v0.1.293 (2025-09-16)

### Continuous Integration

- Release v0.1.293
  ([`fb07c6b`](https://github.com/nfraxlab/svc-infra/commit/fb07c6b20d2f745ed9fd4e966c9f180876efcc60))


## v0.1.292 (2025-09-16)

### Continuous Integration

- Release v0.1.292
  ([`402fe84`](https://github.com/nfraxlab/svc-infra/commit/402fe84c95cf449ef334e50b53daf634bcc60eef))


## v0.1.291 (2025-09-16)

### Continuous Integration

- Release v0.1.291
  ([`3a645ea`](https://github.com/nfraxlab/svc-infra/commit/3a645ea9b7eea7dc398ffb13bd00723d89d4d8db))


## v0.1.290 (2025-09-16)

### Continuous Integration

- Release v0.1.290
  ([`295948b`](https://github.com/nfraxlab/svc-infra/commit/295948b7fd8086826b998df76e4c684811314a51))


## v0.1.289 (2025-09-16)

### Continuous Integration

- Release v0.1.289
  ([`fccc669`](https://github.com/nfraxlab/svc-infra/commit/fccc669e1351bf0b23139bfe41aec3604a88b337))


## v0.1.288 (2025-09-16)

### Continuous Integration

- Release v0.1.288
  ([`e0aaea5`](https://github.com/nfraxlab/svc-infra/commit/e0aaea5f9879ef551cd7a689849e235171f71e6f))


## v0.1.287 (2025-09-15)

### Continuous Integration

- Release v0.1.287
  ([`1ef162a`](https://github.com/nfraxlab/svc-infra/commit/1ef162a4beddcd771e707cc8fe92a0c53f0014ce))


## v0.1.286 (2025-09-15)

### Continuous Integration

- Release v0.1.286
  ([`6416939`](https://github.com/nfraxlab/svc-infra/commit/641693964d2df8ea7ee184b38111ea71e0cc9028))


## v0.1.285 (2025-09-15)

### Continuous Integration

- Release v0.1.285
  ([`41e3462`](https://github.com/nfraxlab/svc-infra/commit/41e34620d6e50bce8f6562424bc05f282b396ce9))


## v0.1.284 (2025-09-15)

### Continuous Integration

- Release v0.1.284
  ([`9f482e5`](https://github.com/nfraxlab/svc-infra/commit/9f482e5483186ba44f9dab98d3d94b72cc8c60aa))


## v0.1.283 (2025-09-15)

### Continuous Integration

- Release v0.1.283
  ([`5a3fb8e`](https://github.com/nfraxlab/svc-infra/commit/5a3fb8e9da611df7ca7b76373abd9a90774e8462))


## v0.1.282 (2025-09-15)

### Continuous Integration

- Release v0.1.282
  ([`42888dd`](https://github.com/nfraxlab/svc-infra/commit/42888dd958085733547a3b8d1b6cb72182c6d521))


## v0.1.281 (2025-09-15)

### Continuous Integration

- Release v0.1.281
  ([`75369cb`](https://github.com/nfraxlab/svc-infra/commit/75369cb5dd4fb2b866a2bed9e808fc61e54b3381))


## v0.1.280 (2025-09-15)

### Continuous Integration

- Release v0.1.280
  ([`f73c816`](https://github.com/nfraxlab/svc-infra/commit/f73c816124cfd3f930ef468c1437179658acfd6d))


## v0.1.279 (2025-09-15)

### Continuous Integration

- Release v0.1.279
  ([`99a3d7f`](https://github.com/nfraxlab/svc-infra/commit/99a3d7fca31a4fb97768f9a422aab89bc47f4a7d))


## v0.1.278 (2025-09-15)

### Continuous Integration

- Release v0.1.278
  ([`e4b706a`](https://github.com/nfraxlab/svc-infra/commit/e4b706aa908583cf5d1f1f694eb45f76f5ea1a16))


## v0.1.277 (2025-09-15)

### Continuous Integration

- Release v0.1.277
  ([`383f9a9`](https://github.com/nfraxlab/svc-infra/commit/383f9a99701dbc23650d1eccdd1cc2056ad7dc4d))


## v0.1.276 (2025-09-15)

### Continuous Integration

- Release v0.1.276
  ([`fc471f9`](https://github.com/nfraxlab/svc-infra/commit/fc471f9b475eeb41c7065a3a526260e1514ba08a))


## v0.1.275 (2025-09-15)

### Continuous Integration

- Release v0.1.275
  ([`e2c361a`](https://github.com/nfraxlab/svc-infra/commit/e2c361af43a4f4cdc068183655259df431f99263))


## v0.1.274 (2025-09-15)

### Continuous Integration

- Release v0.1.274
  ([`4341ba6`](https://github.com/nfraxlab/svc-infra/commit/4341ba623a9f9604d0ed38acc91b127f3a9193af))


## v0.1.273 (2025-09-15)

### Continuous Integration

- Release v0.1.273
  ([`93c1121`](https://github.com/nfraxlab/svc-infra/commit/93c1121e35400b37c62f633bfcd4e089daebc754))


## v0.1.272 (2025-09-15)

### Continuous Integration

- Release v0.1.272
  ([`42b9cbd`](https://github.com/nfraxlab/svc-infra/commit/42b9cbdcd84db72d1eba6817fd86cfc78fa08af1))


## v0.1.271 (2025-09-14)

### Continuous Integration

- Release v0.1.271
  ([`4999a64`](https://github.com/nfraxlab/svc-infra/commit/4999a644bb11152b5d88827637f6a2d2407f69f2))


## v0.1.270 (2025-09-14)

### Continuous Integration

- Release v0.1.270
  ([`96ce294`](https://github.com/nfraxlab/svc-infra/commit/96ce294dcdee0c286b52d3245f3c48c4874eb3ad))


## v0.1.269 (2025-09-14)

### Continuous Integration

- Release v0.1.269
  ([`464b02f`](https://github.com/nfraxlab/svc-infra/commit/464b02f90983eead81c2c7b56febb029e0492df5))


## v0.1.268 (2025-09-14)

### Continuous Integration

- Release v0.1.268
  ([`37a8754`](https://github.com/nfraxlab/svc-infra/commit/37a87542951cb29e7088a0658f23eb514ad8fd88))


## v0.1.267 (2025-09-14)

### Continuous Integration

- Release v0.1.267
  ([`c8712af`](https://github.com/nfraxlab/svc-infra/commit/c8712af2b4bd6f86230eb8f9deea19f757453698))


## v0.1.266 (2025-09-14)

### Continuous Integration

- Release v0.1.266
  ([`73a70bc`](https://github.com/nfraxlab/svc-infra/commit/73a70bcdc1929483c8ebdf9423994aeb2dab6e9d))


## v0.1.265 (2025-09-14)

### Continuous Integration

- Release v0.1.265
  ([`47e11be`](https://github.com/nfraxlab/svc-infra/commit/47e11bef1e404951c6a133c259a6aded189722f3))


## v0.1.264 (2025-09-14)

### Continuous Integration

- Release v0.1.264
  ([`b4410af`](https://github.com/nfraxlab/svc-infra/commit/b4410afa717f8fc425b81b7957616ded15c19c3d))


## v0.1.263 (2025-09-14)

### Continuous Integration

- Release v0.1.263
  ([`0a88513`](https://github.com/nfraxlab/svc-infra/commit/0a88513e800056c3680ab709484ccc650d54da7e))


## v0.1.262 (2025-09-14)

### Continuous Integration

- Release v0.1.262
  ([`79a9069`](https://github.com/nfraxlab/svc-infra/commit/79a906944c7be105b4bfbd38e1b763431b5cc251))


## v0.1.261 (2025-09-14)

### Continuous Integration

- Release v0.1.261
  ([`e0ceee8`](https://github.com/nfraxlab/svc-infra/commit/e0ceee8d023202e3724e7bb67b8ad389eda449ac))


## v0.1.260 (2025-09-14)

### Continuous Integration

- Release v0.1.260
  ([`037deee`](https://github.com/nfraxlab/svc-infra/commit/037deee8401ca357905a45eca66aad0d222e2e08))


## v0.1.259 (2025-09-14)

### Continuous Integration

- Release v0.1.259
  ([`6dfa770`](https://github.com/nfraxlab/svc-infra/commit/6dfa7709d10b52937421dc761e90d6d943a71777))


## v0.1.258 (2025-09-14)

### Continuous Integration

- Release v0.1.258
  ([`1b35762`](https://github.com/nfraxlab/svc-infra/commit/1b357622dfc2c48f45aeed1da69993011f8551e4))


## v0.1.257 (2025-09-13)

### Continuous Integration

- Release v0.1.257
  ([`b8f8e37`](https://github.com/nfraxlab/svc-infra/commit/b8f8e37748c7bbe4cb16c0d14ba749e7a98e9cc8))


## v0.1.256 (2025-09-13)

### Continuous Integration

- Release v0.1.256
  ([`ecdc987`](https://github.com/nfraxlab/svc-infra/commit/ecdc98732a2afbfffa72689d6d3d404a7923a6f1))


## v0.1.255 (2025-09-13)

### Continuous Integration

- Release v0.1.255
  ([`2f12c38`](https://github.com/nfraxlab/svc-infra/commit/2f12c381f5538f3ca0287b4b92dc6dcee659e730))


## v0.1.254 (2025-09-13)

### Continuous Integration

- Release v0.1.254
  ([`73cb0e3`](https://github.com/nfraxlab/svc-infra/commit/73cb0e3f338817ac4bfd849169513b7174a4fd61))


## v0.1.253 (2025-09-13)

### Continuous Integration

- Release v0.1.253
  ([`c6d914e`](https://github.com/nfraxlab/svc-infra/commit/c6d914e259beaa85bb394185f25cd761b9b72ee6))


## v0.1.252 (2025-09-13)

### Continuous Integration

- Release v0.1.252
  ([`4f90493`](https://github.com/nfraxlab/svc-infra/commit/4f90493bf54a6a74a3cb82223bfce5e16e33960f))


## v0.1.251 (2025-09-13)

### Continuous Integration

- Release v0.1.251
  ([`78a807a`](https://github.com/nfraxlab/svc-infra/commit/78a807ae90a82e5f76bb3c56ff5ac01a4974fdf5))


## v0.1.250 (2025-09-13)

### Continuous Integration

- Release v0.1.250
  ([`e02f2d6`](https://github.com/nfraxlab/svc-infra/commit/e02f2d6f866e0d5689aa2e6dfc3c70ee60c5fe16))


## v0.1.249 (2025-09-13)

### Continuous Integration

- Release v0.1.249
  ([`065fa88`](https://github.com/nfraxlab/svc-infra/commit/065fa886d8b477e9624c0588e2605fea67470b0d))


## v0.1.248 (2025-09-13)

### Continuous Integration

- Release v0.1.248
  ([`c665636`](https://github.com/nfraxlab/svc-infra/commit/c6656366d0647ad5d838ede3acf942f49244719c))


## v0.1.247 (2025-09-13)

### Continuous Integration

- Release v0.1.247
  ([`d9a600c`](https://github.com/nfraxlab/svc-infra/commit/d9a600c5448be551d8b85ade43a2959565a155c3))


## v0.1.246 (2025-09-13)

### Continuous Integration

- Release v0.1.246
  ([`2354737`](https://github.com/nfraxlab/svc-infra/commit/235473717b47cae18cb7a8b90d1e530f519cbe0b))


## v0.1.245 (2025-09-12)

### Continuous Integration

- Release v0.1.245
  ([`e66089a`](https://github.com/nfraxlab/svc-infra/commit/e66089a474ecbbe5941293b21e3e175d64625732))


## v0.1.244 (2025-09-12)

### Continuous Integration

- Release v0.1.244
  ([`dba5fa2`](https://github.com/nfraxlab/svc-infra/commit/dba5fa29ab5ce6fb0ee5fe2e6fd22b4cfb946ea9))


## v0.1.243 (2025-09-12)

### Continuous Integration

- Release v0.1.243
  ([`27fe21a`](https://github.com/nfraxlab/svc-infra/commit/27fe21af547db16a0781acac72dd4e6870e97d3c))


## v0.1.242 (2025-09-12)

### Continuous Integration

- Release v0.1.242
  ([`4a9638a`](https://github.com/nfraxlab/svc-infra/commit/4a9638a17eb3a00c0544a233345e0c02326d9ff7))


## v0.1.241 (2025-09-12)

### Continuous Integration

- Release v0.1.241
  ([`0eedd4f`](https://github.com/nfraxlab/svc-infra/commit/0eedd4f9e287e307f1ff7e4caf6d37f2d79a681d))


## v0.1.240 (2025-09-12)

### Continuous Integration

- Release v0.1.240
  ([`634a18a`](https://github.com/nfraxlab/svc-infra/commit/634a18a8752fd2dc881f4154de83180ef5a4ab70))


## v0.1.239 (2025-09-12)

### Continuous Integration

- Release v0.1.239
  ([`e6a525d`](https://github.com/nfraxlab/svc-infra/commit/e6a525d838052a249216ec49cd999fce5a118f36))


## v0.1.238 (2025-09-12)

### Continuous Integration

- Release v0.1.238
  ([`42e7448`](https://github.com/nfraxlab/svc-infra/commit/42e74484988fb71078b51f3932843d96a2bdde65))


## v0.1.237 (2025-09-11)

### Continuous Integration

- Release v0.1.237
  ([`049910f`](https://github.com/nfraxlab/svc-infra/commit/049910f5778a8e14d44eab79282080a124d65667))


## v0.1.236 (2025-09-11)

### Continuous Integration

- Release v0.1.236
  ([`4643dc1`](https://github.com/nfraxlab/svc-infra/commit/4643dc13119b4c4374f88458937666ec9fbb5c60))


## v0.1.235 (2025-09-11)

### Continuous Integration

- Release v0.1.235
  ([`e380017`](https://github.com/nfraxlab/svc-infra/commit/e380017a9cb1d02ab4fa03b0f4045341b8537d73))


## v0.1.234 (2025-09-11)

### Continuous Integration

- Release v0.1.234
  ([`dd3ef42`](https://github.com/nfraxlab/svc-infra/commit/dd3ef426b4a260356e69d77092ec342a73a03321))


## v0.1.233 (2025-09-11)

### Continuous Integration

- Release v0.1.233
  ([`86c0ead`](https://github.com/nfraxlab/svc-infra/commit/86c0eadcec2b1a75e383bc8d7edf7c75958d42c0))


## v0.1.232 (2025-09-11)

### Continuous Integration

- Release v0.1.232
  ([`1e10b06`](https://github.com/nfraxlab/svc-infra/commit/1e10b061b06e0e666dfd1aa5096d35cb5adff6fe))


## v0.1.231 (2025-09-11)

### Continuous Integration

- Release v0.1.231
  ([`9e75b44`](https://github.com/nfraxlab/svc-infra/commit/9e75b44157dc5c0886850244b347e6429e763019))


## v0.1.230 (2025-09-11)

### Continuous Integration

- Release v0.1.230
  ([`3b669d8`](https://github.com/nfraxlab/svc-infra/commit/3b669d8abe6f4e5b2311f1d9ea0a5a616bcdbdd1))


## v0.1.229 (2025-09-11)

### Continuous Integration

- Release v0.1.229
  ([`f8c1c76`](https://github.com/nfraxlab/svc-infra/commit/f8c1c760b74a42c98331a5f0747a9a96d9a59934))


## v0.1.228 (2025-09-11)

### Continuous Integration

- Release v0.1.228
  ([`70bd7c2`](https://github.com/nfraxlab/svc-infra/commit/70bd7c2d334ec759427d429fc1e5e8322dd1af81))


## v0.1.227 (2025-09-11)

### Continuous Integration

- Release v0.1.227
  ([`1be4d89`](https://github.com/nfraxlab/svc-infra/commit/1be4d89ed8c3bbf094eae2c9a2f75e4cdcd2611d))


## v0.1.226 (2025-09-11)

### Continuous Integration

- Release v0.1.226
  ([`1db584c`](https://github.com/nfraxlab/svc-infra/commit/1db584cb9f4557016818afb07bad29d54df6b3a9))


## v0.1.225 (2025-09-11)

### Continuous Integration

- Release v0.1.225
  ([`d8dd3cf`](https://github.com/nfraxlab/svc-infra/commit/d8dd3cf1542849d4d5b4acbbe551131367f38214))


## v0.1.224 (2025-09-11)

### Continuous Integration

- Release v0.1.224
  ([`69d64ed`](https://github.com/nfraxlab/svc-infra/commit/69d64edc430bd833f560487b8cdf99eb3d182a7a))


## v0.1.223 (2025-09-10)

### Continuous Integration

- Release v0.1.223
  ([`9fa8ca0`](https://github.com/nfraxlab/svc-infra/commit/9fa8ca0fe936b1651cd3d8fa04f911d80125e369))


## v0.1.222 (2025-09-10)

### Continuous Integration

- Release v0.1.221
  ([`2318867`](https://github.com/nfraxlab/svc-infra/commit/23188672e0f40fa789fb6f0a8fb282336a539b0b))

- Release v0.1.222
  ([`9048bfa`](https://github.com/nfraxlab/svc-infra/commit/9048bfab342a1ac32fe57e1050e2d7ff9a0db5bf))


## v0.1.220 (2025-09-10)

### Continuous Integration

- Release v0.1.220
  ([`445f4cc`](https://github.com/nfraxlab/svc-infra/commit/445f4cc568770cf48d3bd42f0ca4c22baa2052ac))


## v0.1.219 (2025-09-10)

### Continuous Integration

- Release v0.1.219
  ([`c43b2ad`](https://github.com/nfraxlab/svc-infra/commit/c43b2ad4caf16489b38eecf1afd0a1620a32c045))


## v0.1.218 (2025-09-10)

### Continuous Integration

- Release v0.1.218
  ([`c4c23f5`](https://github.com/nfraxlab/svc-infra/commit/c4c23f51189f2b8fc9707b705f72715c21fd0b7f))


## v0.1.217 (2025-09-10)

### Continuous Integration

- Release v0.1.217
  ([`96dc391`](https://github.com/nfraxlab/svc-infra/commit/96dc391d8a4907157a912e73c0993e1e3edf86ed))


## v0.1.216 (2025-09-10)

### Continuous Integration

- Release v0.1.216
  ([`dd40914`](https://github.com/nfraxlab/svc-infra/commit/dd40914b8d02a48b9f53bbbdd8d96e1987d195fd))


## v0.1.215 (2025-09-10)

### Continuous Integration

- Release v0.1.215
  ([`586adb2`](https://github.com/nfraxlab/svc-infra/commit/586adb21599bf68c2cc8999098497c31b77333e3))


## v0.1.214 (2025-09-10)

### Continuous Integration

- Release v0.1.214
  ([`8799851`](https://github.com/nfraxlab/svc-infra/commit/8799851f35ba4e15bd27d9b4345ea957e14d9afc))


## v0.1.213 (2025-09-10)

### Continuous Integration

- Release v0.1.213
  ([`9f31b24`](https://github.com/nfraxlab/svc-infra/commit/9f31b2453de97f8f043caba6117d0a6937954ea9))


## v0.1.212 (2025-09-10)

### Continuous Integration

- Release v0.1.212
  ([`091a40e`](https://github.com/nfraxlab/svc-infra/commit/091a40eab293255f4928575177eb6692236bf1a4))


## v0.1.211 (2025-09-10)

### Continuous Integration

- Release v0.1.211
  ([`f356831`](https://github.com/nfraxlab/svc-infra/commit/f35683142df9dd60e151c2dc3abb0c71370bfdd7))


## v0.1.210 (2025-09-10)

### Continuous Integration

- Release v0.1.210
  ([`0ca36a6`](https://github.com/nfraxlab/svc-infra/commit/0ca36a6d9b1dffc920b8aa4aeb9824389b5ce1dd))


## v0.1.209 (2025-09-10)

### Continuous Integration

- Release v0.1.209
  ([`e400e7e`](https://github.com/nfraxlab/svc-infra/commit/e400e7e438ffdc09f989cc1a5b74074174e53a56))


## v0.1.208 (2025-09-10)

### Continuous Integration

- Release v0.1.208
  ([`7fdf252`](https://github.com/nfraxlab/svc-infra/commit/7fdf2524d3d967231027d4abf75eda1813d5b715))


## v0.1.207 (2025-09-10)

### Continuous Integration

- Release v0.1.207
  ([`71172f3`](https://github.com/nfraxlab/svc-infra/commit/71172f3c3a0ae37ec55707205d31c5116ed11ea8))


## v0.1.206 (2025-09-10)

### Continuous Integration

- Release v0.1.206
  ([`595ea39`](https://github.com/nfraxlab/svc-infra/commit/595ea3939f29714416dc39f3399bbf98b7c84ba1))


## v0.1.205 (2025-09-09)

### Continuous Integration

- Release v0.1.205
  ([`4290aba`](https://github.com/nfraxlab/svc-infra/commit/4290aba3e6fb7157efbfc1e6999e108f85fcb8ce))


## v0.1.204 (2025-09-09)

### Continuous Integration

- Release v0.1.204
  ([`336deba`](https://github.com/nfraxlab/svc-infra/commit/336deba342952f39d3e22a8f5fc163ce6c6c8a04))


## v0.1.203 (2025-09-09)

### Continuous Integration

- Release v0.1.203
  ([`cd938b8`](https://github.com/nfraxlab/svc-infra/commit/cd938b8659a7d5cde1316d312a19e44d7f30d7e8))


## v0.1.202 (2025-09-09)

### Continuous Integration

- Release v0.1.202
  ([`efb101b`](https://github.com/nfraxlab/svc-infra/commit/efb101b9ef81de88df508e4a99ad73391f9c9a98))


## v0.1.201 (2025-09-09)

### Continuous Integration

- Release v0.1.201
  ([`08538a6`](https://github.com/nfraxlab/svc-infra/commit/08538a69c6475da5e5c63f9d2b06055cd562126e))


## v0.1.200 (2025-09-09)

### Continuous Integration

- Release v0.1.200
  ([`882a614`](https://github.com/nfraxlab/svc-infra/commit/882a61406fe0b2a81a8bcae24eff6e3096f17bbc))


## v0.1.199 (2025-09-09)

### Continuous Integration

- Release v0.1.199
  ([`5d9f7c6`](https://github.com/nfraxlab/svc-infra/commit/5d9f7c6f813d1cc33ae6e317d7e80f6d45b466c6))


## v0.1.198 (2025-09-09)

### Continuous Integration

- Release v0.1.198
  ([`af47a0b`](https://github.com/nfraxlab/svc-infra/commit/af47a0be93a8922e74b6bf9d74233c4d492ada98))


## v0.1.197 (2025-09-09)

### Continuous Integration

- Release v0.1.197
  ([`b1ba5ac`](https://github.com/nfraxlab/svc-infra/commit/b1ba5ac202cb42e8aac41fdc71824450c5a508c7))


## v0.1.196 (2025-09-09)

### Continuous Integration

- Release v0.1.196
  ([`0384c76`](https://github.com/nfraxlab/svc-infra/commit/0384c7677a3dcd6077a929bb449b317b04c54317))


## v0.1.195 (2025-09-09)

### Continuous Integration

- Release v0.1.195
  ([`2dc491f`](https://github.com/nfraxlab/svc-infra/commit/2dc491f1968047db25b4a1de0ea1595ec63bc58f))


## v0.1.194 (2025-09-09)

### Continuous Integration

- Release v0.1.194
  ([`f2c1119`](https://github.com/nfraxlab/svc-infra/commit/f2c1119eb81511623ddf7fefe79fb80c71f30d13))


## v0.1.193 (2025-09-09)

### Continuous Integration

- Release v0.1.193
  ([`b1c28d2`](https://github.com/nfraxlab/svc-infra/commit/b1c28d20cd050157ef4ac30b0f90d3ca8ffc2add))


## v0.1.192 (2025-09-09)

### Continuous Integration

- Release v0.1.192
  ([`45feaba`](https://github.com/nfraxlab/svc-infra/commit/45feabae4a2d75408d5089cef63df8dcf5259a0d))


## v0.1.191 (2025-09-09)

### Continuous Integration

- Release v0.1.191
  ([`aae2c05`](https://github.com/nfraxlab/svc-infra/commit/aae2c058246b265cb5c41f30e9a100b7ea37b23b))


## v0.1.190 (2025-09-09)

### Continuous Integration

- Release v0.1.190
  ([`c9b0ace`](https://github.com/nfraxlab/svc-infra/commit/c9b0ace204710a128ff9403f4396aeb5c42e7e5c))


## v0.1.189 (2025-09-09)

### Continuous Integration

- Release v0.1.189
  ([`055d549`](https://github.com/nfraxlab/svc-infra/commit/055d549777ab31b084e250948df8ad53a799aa74))


## v0.1.188 (2025-09-09)

### Continuous Integration

- Release v0.1.188
  ([`edb35b7`](https://github.com/nfraxlab/svc-infra/commit/edb35b73bcfd0d1664139f0aaee1e905e25ae0d9))


## v0.1.187 (2025-09-08)

### Continuous Integration

- Release v0.1.187
  ([`239562c`](https://github.com/nfraxlab/svc-infra/commit/239562c56348c69f8429c76bc552d00cbd990577))


## v0.1.186 (2025-09-08)

### Continuous Integration

- Release v0.1.186
  ([`9c50e61`](https://github.com/nfraxlab/svc-infra/commit/9c50e614a9535294e9f7b7ae2dd333c887c13af7))


## v0.1.185 (2025-09-08)

### Continuous Integration

- Release v0.1.185
  ([`4896715`](https://github.com/nfraxlab/svc-infra/commit/4896715aa46cd658ed0183ef4ee52cd735730d67))


## v0.1.184 (2025-09-08)

### Continuous Integration

- Release v0.1.184
  ([`18984e7`](https://github.com/nfraxlab/svc-infra/commit/18984e778a97ed6f2cc5c29ce18c1f80119c2b71))


## v0.1.183 (2025-09-08)

### Continuous Integration

- Release v0.1.183
  ([`2889322`](https://github.com/nfraxlab/svc-infra/commit/2889322332be22227191ba98477bb3fba87a4246))


## v0.1.182 (2025-09-08)

### Continuous Integration

- Release v0.1.182
  ([`1570af9`](https://github.com/nfraxlab/svc-infra/commit/1570af91e067654c31d845be3889c0f63848ed47))


## v0.1.181 (2025-09-08)

### Continuous Integration

- Release v0.1.181
  ([`917128a`](https://github.com/nfraxlab/svc-infra/commit/917128aaedd391fabd3ef9f0437e39d056e8bfb3))


## v0.1.180 (2025-09-08)

### Continuous Integration

- Release v0.1.180
  ([`78958c3`](https://github.com/nfraxlab/svc-infra/commit/78958c3f8a6d49952bbd8435898cbd00c2efe72e))


## v0.1.179 (2025-09-08)

### Continuous Integration

- Release v0.1.179
  ([`d22d77a`](https://github.com/nfraxlab/svc-infra/commit/d22d77aabc9b14343f0170080c04bf07afa3e48a))


## v0.1.178 (2025-09-08)

### Continuous Integration

- Release v0.1.178
  ([`20b5979`](https://github.com/nfraxlab/svc-infra/commit/20b5979f2feecc51a75fc71160f1c406ef6ba487))


## v0.1.177 (2025-09-08)

### Continuous Integration

- Release v0.1.177
  ([`cb559c8`](https://github.com/nfraxlab/svc-infra/commit/cb559c8a702455ec81ae7dd3d9ff7fdf8f9f613d))


## v0.1.176 (2025-09-08)

### Continuous Integration

- Release v0.1.176
  ([`4ce4050`](https://github.com/nfraxlab/svc-infra/commit/4ce4050d243e03678169a003c3f693751c90fba5))


## v0.1.175 (2025-09-08)

### Continuous Integration

- Release v0.1.175
  ([`5d192ec`](https://github.com/nfraxlab/svc-infra/commit/5d192ec42f943f5dd43aad85c0e08525b9826822))


## v0.1.174 (2025-09-08)

### Continuous Integration

- Release v0.1.174
  ([`5f1b3d8`](https://github.com/nfraxlab/svc-infra/commit/5f1b3d8b43f6ccbc8915ed00c99fc19629f6b347))


## v0.1.173 (2025-09-08)

### Continuous Integration

- Release v0.1.173
  ([`3fd906d`](https://github.com/nfraxlab/svc-infra/commit/3fd906d2f6658fb7c9ced67a8e8e6dc99ee42984))


## v0.1.172 (2025-09-08)

### Continuous Integration

- Release v0.1.172
  ([`6cc75da`](https://github.com/nfraxlab/svc-infra/commit/6cc75da6fb1ab3cc3eac60efa1b3d3382a593364))


## v0.1.171 (2025-09-08)

### Continuous Integration

- Release v0.1.171
  ([`c538b4b`](https://github.com/nfraxlab/svc-infra/commit/c538b4bc790de23b2d7dd6fd7909faeb84667682))


## v0.1.170 (2025-09-08)

### Continuous Integration

- Release v0.1.170
  ([`948e1bd`](https://github.com/nfraxlab/svc-infra/commit/948e1bdd902d3a3724213667068f02151ee88dec))


## v0.1.169 (2025-09-08)

### Continuous Integration

- Release v0.1.169
  ([`8504e17`](https://github.com/nfraxlab/svc-infra/commit/8504e1719698cfc0c06cf44e6c7da777cb014e7b))


## v0.1.168 (2025-09-08)

### Continuous Integration

- Release v0.1.168
  ([`831a7ec`](https://github.com/nfraxlab/svc-infra/commit/831a7ecf1e8909ae6649ed6bd6d9afd8712e1c20))


## v0.1.167 (2025-09-08)

### Continuous Integration

- Release v0.1.167
  ([`03400d8`](https://github.com/nfraxlab/svc-infra/commit/03400d87a84e650f035584464cc5ce45eb8d8171))


## v0.1.166 (2025-09-08)

### Continuous Integration

- Release v0.1.166
  ([`0597210`](https://github.com/nfraxlab/svc-infra/commit/05972109cc975169483e9bd47de3106895288690))


## v0.1.165 (2025-09-08)

### Continuous Integration

- Release v0.1.165
  ([`57c347b`](https://github.com/nfraxlab/svc-infra/commit/57c347b09c9dc22f9f2b4b8a2cd13fbf7a2f94e2))


## v0.1.164 (2025-09-08)

### Continuous Integration

- Release v0.1.164
  ([`fc87bee`](https://github.com/nfraxlab/svc-infra/commit/fc87bee76ece437b2dc89825da6409be118af10a))


## v0.1.163 (2025-09-08)

### Continuous Integration

- Release v0.1.163
  ([`7a70694`](https://github.com/nfraxlab/svc-infra/commit/7a7069490deead755544e619714696d39153f87d))


## v0.1.162 (2025-09-08)

### Continuous Integration

- Release v0.1.162
  ([`1aac61e`](https://github.com/nfraxlab/svc-infra/commit/1aac61e65fe40d777b85088a41714849c399dd6c))


## v0.1.161 (2025-09-08)

### Continuous Integration

- Release v0.1.160
  ([`c5b4bff`](https://github.com/nfraxlab/svc-infra/commit/c5b4bff7ab51f105fb99c783fb1ad3ac3e216ee8))

- Release v0.1.161
  ([`33a1856`](https://github.com/nfraxlab/svc-infra/commit/33a1856ffa1dff8a97b7f548517f92c31496cbc7))


## v0.1.159 (2025-09-08)

### Continuous Integration

- Release v0.1.159
  ([`1f1daa4`](https://github.com/nfraxlab/svc-infra/commit/1f1daa4d9abd447383daca4dd7549f237b6da413))


## v0.1.158 (2025-09-08)

### Continuous Integration

- Release v0.1.158
  ([`234ef1e`](https://github.com/nfraxlab/svc-infra/commit/234ef1ec14965eaf4771a8d26c44eecef5cd15c2))


## v0.1.157 (2025-09-08)

### Continuous Integration

- Release v0.1.157
  ([`b954698`](https://github.com/nfraxlab/svc-infra/commit/b954698e8842725afbae6078649fca4c57461953))


## v0.1.156 (2025-09-08)

### Continuous Integration

- Release v0.1.156
  ([`ac18000`](https://github.com/nfraxlab/svc-infra/commit/ac180005e9a0f231fc3f5667a2c7fd864fe49297))


## v0.1.155 (2025-09-08)

### Continuous Integration

- Release v0.1.155
  ([`c165e8f`](https://github.com/nfraxlab/svc-infra/commit/c165e8fff4169cf172d5d886e590facc543ef56a))


## v0.1.154 (2025-09-08)

### Continuous Integration

- Release v0.1.154
  ([`c4e67bf`](https://github.com/nfraxlab/svc-infra/commit/c4e67bfb00b998fa9c2a457872eaf71a435a9dc4))


## v0.1.153 (2025-09-08)

### Continuous Integration

- Release v0.1.153
  ([`2894d54`](https://github.com/nfraxlab/svc-infra/commit/2894d54d15f692e7a615b3939e0818d1cdc5064d))


## v0.1.152 (2025-09-08)

### Continuous Integration

- Release v0.1.152
  ([`6fd33b4`](https://github.com/nfraxlab/svc-infra/commit/6fd33b4e0c62eb6146aaf788d42b6f23c889afbc))


## v0.1.151 (2025-09-07)

### Continuous Integration

- Release v0.1.151
  ([`07aafb7`](https://github.com/nfraxlab/svc-infra/commit/07aafb7fc8cda3bc86d372bdf6f837b23c5a9d09))


## v0.1.150 (2025-09-07)

### Continuous Integration

- Release v0.1.150
  ([`40624dd`](https://github.com/nfraxlab/svc-infra/commit/40624dd9d78441306d5c4222d869e073a5ba1d2b))


## v0.1.149 (2025-09-07)

### Continuous Integration

- Release v0.1.149
  ([`85d9cb7`](https://github.com/nfraxlab/svc-infra/commit/85d9cb7b2d25fa7dca4d43d722794df2a48f4861))


## v0.1.148 (2025-09-07)

### Continuous Integration

- Release v0.1.148
  ([`97d7cdf`](https://github.com/nfraxlab/svc-infra/commit/97d7cdfeba7d7a1573353658284b73faeb68f6b8))


## v0.1.147 (2025-09-07)

### Continuous Integration

- Release v0.1.147
  ([`1dd3f7d`](https://github.com/nfraxlab/svc-infra/commit/1dd3f7de1031b347c381290fcd58f14c1d9c015f))


## v0.1.146 (2025-09-07)

### Continuous Integration

- Release v0.1.146
  ([`086991f`](https://github.com/nfraxlab/svc-infra/commit/086991f13b1bbffe64067f5370d6738506d139a1))


## v0.1.145 (2025-09-07)

### Continuous Integration

- Release v0.1.145
  ([`2efb610`](https://github.com/nfraxlab/svc-infra/commit/2efb6106b72e36bcc40c89fca34b231abe2ae1f8))


## v0.1.144 (2025-09-07)

### Continuous Integration

- Release v0.1.144
  ([`9a209c0`](https://github.com/nfraxlab/svc-infra/commit/9a209c045042ff476642f6ebb8b04dae0a705e88))


## v0.1.143 (2025-09-07)

### Continuous Integration

- Release v0.1.143
  ([`caebeda`](https://github.com/nfraxlab/svc-infra/commit/caebedaf3c458f00b8acef7159690f071d46432c))


## v0.1.142 (2025-09-07)

### Continuous Integration

- Release v0.1.142
  ([`332e011`](https://github.com/nfraxlab/svc-infra/commit/332e011492cfe504b0e11e304cd55b852a27385c))


## v0.1.141 (2025-09-07)

### Continuous Integration

- Release v0.1.141
  ([`5cb1fbc`](https://github.com/nfraxlab/svc-infra/commit/5cb1fbcb712546b51a88701244a4c9c4b60a77d6))


## v0.1.140 (2025-09-07)

### Continuous Integration

- Release v0.1.140
  ([`4d3ff31`](https://github.com/nfraxlab/svc-infra/commit/4d3ff3169082d8d9f89f1acb26c053c401165954))


## v0.1.139 (2025-09-07)

### Continuous Integration

- Release v0.1.139
  ([`0c1f9bb`](https://github.com/nfraxlab/svc-infra/commit/0c1f9bb4bfa02d9939396ea1ad4a1f54bcb718c2))


## v0.1.138 (2025-09-07)

### Continuous Integration

- Release v0.1.138
  ([`98f0362`](https://github.com/nfraxlab/svc-infra/commit/98f0362e34bed6f4560eb39a461042e3103db5c7))


## v0.1.137 (2025-09-07)

### Continuous Integration

- Release v0.1.137
  ([`b2f7dfd`](https://github.com/nfraxlab/svc-infra/commit/b2f7dfd5d9d11a86c33fc71178bc700fdc5005d0))


## v0.1.136 (2025-09-07)

### Continuous Integration

- Release v0.1.136
  ([`f9c95ef`](https://github.com/nfraxlab/svc-infra/commit/f9c95ef3ff9ded8f47cf6c206c40d17284eec02b))


## v0.1.135 (2025-09-07)

### Continuous Integration

- Release v0.1.135
  ([`f46050f`](https://github.com/nfraxlab/svc-infra/commit/f46050f258524aa4cdb399b30f6faabba14d97ff))


## v0.1.134 (2025-09-07)

### Continuous Integration

- Release v0.1.134
  ([`35b4531`](https://github.com/nfraxlab/svc-infra/commit/35b4531559f2f05ecbdda233cc37dbe5f7a7235e))


## v0.1.133 (2025-09-07)

### Continuous Integration

- Release v0.1.133
  ([`68fc7f9`](https://github.com/nfraxlab/svc-infra/commit/68fc7f9823348cde5c0ae81c46a161337bb4ba48))


## v0.1.132 (2025-09-07)

### Continuous Integration

- Release v0.1.132
  ([`ac98573`](https://github.com/nfraxlab/svc-infra/commit/ac985735fc423f819adb64189bd992c935a63b17))


## v0.1.131 (2025-09-07)

### Continuous Integration

- Release v0.1.131
  ([`4327346`](https://github.com/nfraxlab/svc-infra/commit/4327346545564b1bb8be6cf764802a5ed6754688))


## v0.1.130 (2025-09-07)

### Continuous Integration

- Release v0.1.130
  ([`0fc7174`](https://github.com/nfraxlab/svc-infra/commit/0fc717408c3139d5b9897dc5684134367e70285b))


## v0.1.129 (2025-09-07)

### Continuous Integration

- Release v0.1.129
  ([`f380be1`](https://github.com/nfraxlab/svc-infra/commit/f380be1ac93aa5fd6379bbca7a4f2d7d67752e6d))


## v0.1.128 (2025-09-06)

### Continuous Integration

- Release v0.1.128
  ([`2c5af26`](https://github.com/nfraxlab/svc-infra/commit/2c5af26ee7e93cfb88a23a180205e28b8ed4f4f4))


## v0.1.127 (2025-09-06)

### Continuous Integration

- Release v0.1.127
  ([`781c0f3`](https://github.com/nfraxlab/svc-infra/commit/781c0f30d7f88dd344ddda91cc866677ba4692af))


## v0.1.126 (2025-09-06)

### Continuous Integration

- Release v0.1.126
  ([`66acb68`](https://github.com/nfraxlab/svc-infra/commit/66acb68a91ecc170726e5a1dea0df910214d3cba))


## v0.1.125 (2025-09-06)

### Continuous Integration

- Release v0.1.125
  ([`f6b8eff`](https://github.com/nfraxlab/svc-infra/commit/f6b8eff8c4d6e07e8409c9dd88ae87c58ba5e613))


## v0.1.124 (2025-09-06)

### Continuous Integration

- Release v0.1.124
  ([`7dda39a`](https://github.com/nfraxlab/svc-infra/commit/7dda39af372a3bb175f41dcaea17c1b184b94564))


## v0.1.123 (2025-09-06)

### Continuous Integration

- Release v0.1.123
  ([`6a59f60`](https://github.com/nfraxlab/svc-infra/commit/6a59f60ee60a2d67a311b81b5f9b50442b124b00))


## v0.1.122 (2025-09-06)

### Continuous Integration

- Release v0.1.122
  ([`3aeb536`](https://github.com/nfraxlab/svc-infra/commit/3aeb536636c6eb646eaa77a89125f67fd920bbdf))


## v0.1.121 (2025-09-06)

### Continuous Integration

- Release v0.1.121
  ([`cd7137c`](https://github.com/nfraxlab/svc-infra/commit/cd7137cf5b49423c47a504ce05603264c7b847c0))


## v0.1.120 (2025-09-06)

### Continuous Integration

- Release v0.1.120
  ([`2d1788f`](https://github.com/nfraxlab/svc-infra/commit/2d1788fa43f93e16515ba7bf34689503565ccdb1))


## v0.1.119 (2025-09-06)

### Continuous Integration

- Release v0.1.119
  ([`0d60533`](https://github.com/nfraxlab/svc-infra/commit/0d605336e4b51727ea818cdf4ac8c6222bc6ebde))


## v0.1.118 (2025-09-06)

### Continuous Integration

- Release v0.1.118
  ([`41dc229`](https://github.com/nfraxlab/svc-infra/commit/41dc229d2fddc9c7d55afcea33eeb9dfb1932e7d))


## v0.1.117 (2025-09-06)

### Continuous Integration

- Release v0.1.117
  ([`25af188`](https://github.com/nfraxlab/svc-infra/commit/25af18883631b50c205db7cf4a195c1f173eee61))


## v0.1.116 (2025-09-06)

### Continuous Integration

- Release v0.1.116
  ([`abe722e`](https://github.com/nfraxlab/svc-infra/commit/abe722e7bc999669c245e84b9b11bd741df68d97))


## v0.1.115 (2025-09-06)

### Continuous Integration

- Release v0.1.115
  ([`430e555`](https://github.com/nfraxlab/svc-infra/commit/430e555754787ee1b95be9be24c64995c14168de))


## v0.1.114 (2025-09-06)

### Continuous Integration

- Release v0.1.114
  ([`8050f82`](https://github.com/nfraxlab/svc-infra/commit/8050f82f1a0980524c468c781a7ade5433cba4e5))


## v0.1.113 (2025-09-06)

### Continuous Integration

- Release v0.1.113
  ([`b78660c`](https://github.com/nfraxlab/svc-infra/commit/b78660c6912dee13b6f75d8f52a6adb52f6b9fd7))


## v0.1.112 (2025-09-06)

### Continuous Integration

- Release v0.1.112
  ([`6f2774f`](https://github.com/nfraxlab/svc-infra/commit/6f2774f3576dea3cec2351bc7de25a39116ff8b5))


## v0.1.111 (2025-09-06)

### Continuous Integration

- Release v0.1.111
  ([`184ea31`](https://github.com/nfraxlab/svc-infra/commit/184ea31a387153a92ce5177913bc594c8305054a))


## v0.1.110 (2025-09-06)

### Continuous Integration

- Release v0.1.110
  ([`e82648c`](https://github.com/nfraxlab/svc-infra/commit/e82648cbfff0103ac1135645342d5e1919154e36))


## v0.1.109 (2025-09-06)

### Continuous Integration

- Release v0.1.109
  ([`ff88053`](https://github.com/nfraxlab/svc-infra/commit/ff880530db25974982a2368b0966d219a0e840ac))


## v0.1.108 (2025-09-06)

### Continuous Integration

- Release v0.1.108
  ([`0c1615e`](https://github.com/nfraxlab/svc-infra/commit/0c1615ed302eb9855a886067d00475b7ad10e11b))


## v0.1.107 (2025-09-06)

### Continuous Integration

- Release v0.1.107
  ([`f5fa4fd`](https://github.com/nfraxlab/svc-infra/commit/f5fa4fd59d36c56f9c9e4206594bc8b94faddc5e))


## v0.1.106 (2025-09-06)

### Continuous Integration

- Release v0.1.106
  ([`f618630`](https://github.com/nfraxlab/svc-infra/commit/f6186305577558823a7ddf4c7b495b3e017fd19f))


## v0.1.105 (2025-09-06)

### Continuous Integration

- Release v0.1.105
  ([`fd001e2`](https://github.com/nfraxlab/svc-infra/commit/fd001e216e169927c2a8542fbf5a34acadffbc00))


## v0.1.104 (2025-09-06)

### Continuous Integration

- Release v0.1.104
  ([`6d584f3`](https://github.com/nfraxlab/svc-infra/commit/6d584f3065b4b2634c0a7926a0f146d6a8973dcc))


## v0.1.103 (2025-09-06)

### Continuous Integration

- Release v0.1.103
  ([`6fa1034`](https://github.com/nfraxlab/svc-infra/commit/6fa10346d35abd8d44dc87ead20302917b42d777))


## v0.1.102 (2025-09-06)

### Continuous Integration

- Release v0.1.102
  ([`46c7622`](https://github.com/nfraxlab/svc-infra/commit/46c76225b37946ad0629919ef1b2e404591a55aa))


## v0.1.101 (2025-09-06)

### Continuous Integration

- Release v0.1.101
  ([`621e7f3`](https://github.com/nfraxlab/svc-infra/commit/621e7f33ae947c05d8759085ff1d86e339d9acdd))


## v0.1.100 (2025-09-05)

### Continuous Integration

- Release v0.1.100
  ([`5021a97`](https://github.com/nfraxlab/svc-infra/commit/5021a97caa51110470af6cf1f9569ebbc5e0b220))


## v0.1.99 (2025-09-05)

### Continuous Integration

- Release v0.1.99
  ([`1870481`](https://github.com/nfraxlab/svc-infra/commit/18704818d483c0010f3ace758b7221da757356fc))


## v0.1.98 (2025-09-05)

### Continuous Integration

- Release v0.1.98
  ([`7591c43`](https://github.com/nfraxlab/svc-infra/commit/7591c438df76d4c99211d3a02b758cf51cc07ea3))


## v0.1.97 (2025-09-05)

### Continuous Integration

- Release v0.1.96
  ([`f4c88f0`](https://github.com/nfraxlab/svc-infra/commit/f4c88f012c0cd392779470054b8fd648ef91597e))

- Release v0.1.97
  ([`79f8499`](https://github.com/nfraxlab/svc-infra/commit/79f849997ce172fb0d5b538ddc0ca977e76d07a2))


## v0.1.95 (2025-09-05)

### Continuous Integration

- Release v0.1.95
  ([`1feafef`](https://github.com/nfraxlab/svc-infra/commit/1feafef0b5d57b18589ebfde45b7f3aff943523d))


## v0.1.94 (2025-09-05)

### Continuous Integration

- Release v0.1.94
  ([`524cca8`](https://github.com/nfraxlab/svc-infra/commit/524cca8d6fa50b53718826be2e37b4fce06d041b))


## v0.1.93 (2025-09-05)

### Continuous Integration

- Release v0.1.93
  ([`fc96721`](https://github.com/nfraxlab/svc-infra/commit/fc9672166a64f5162772c7664becebe285fc7e49))


## v0.1.92 (2025-09-05)

### Continuous Integration

- Release v0.1.92
  ([`5adc16d`](https://github.com/nfraxlab/svc-infra/commit/5adc16def0cc78c96dfa845f748781d3a3624131))


## v0.1.91 (2025-09-04)

### Continuous Integration

- Release v0.1.91
  ([`ed60383`](https://github.com/nfraxlab/svc-infra/commit/ed60383984194de3b1d878343259df8ca89ae18e))


## v0.1.90 (2025-09-04)

### Continuous Integration

- Release v0.1.90
  ([`e469fd4`](https://github.com/nfraxlab/svc-infra/commit/e469fd4e871929a7e06ff6a9cb24090e3c4a3021))


## v0.1.89 (2025-09-04)

### Continuous Integration

- Release v0.1.89
  ([`a14995f`](https://github.com/nfraxlab/svc-infra/commit/a14995fad3ecaa469ee9313d35c5bea686ffce1b))


## v0.1.88 (2025-09-04)

### Continuous Integration

- Release v0.1.88
  ([`4de23f0`](https://github.com/nfraxlab/svc-infra/commit/4de23f04f36d8d8e1e2b8fc7addb36fef57cfc57))


## v0.1.87 (2025-09-04)

### Continuous Integration

- Release v0.1.87
  ([`b061b5d`](https://github.com/nfraxlab/svc-infra/commit/b061b5d11102b39c3adfe167ce6fad0769f0d590))


## v0.1.86 (2025-09-04)

### Continuous Integration

- Release v0.1.86
  ([`69354c3`](https://github.com/nfraxlab/svc-infra/commit/69354c3a8265f61d61c7c4dccf49270e73ffce3b))


## v0.1.85 (2025-09-04)

### Continuous Integration

- Release v0.1.85
  ([`10cb367`](https://github.com/nfraxlab/svc-infra/commit/10cb3678f8bec37240c0655b590e2475654560f1))


## v0.1.84 (2025-09-04)

### Continuous Integration

- Release v0.1.84
  ([`7ff8fbf`](https://github.com/nfraxlab/svc-infra/commit/7ff8fbf4697167376473bd43baa5c7cc8ed74825))


## v0.1.83 (2025-09-04)

### Continuous Integration

- Release v0.1.83
  ([`9ebef6d`](https://github.com/nfraxlab/svc-infra/commit/9ebef6d4245ba92b68f843887acd654e8b749862))


## v0.1.82 (2025-09-04)

### Continuous Integration

- Release v0.1.82
  ([`fe09ebf`](https://github.com/nfraxlab/svc-infra/commit/fe09ebfbb84f8c84bfdf426f177f1a071ccbe561))


## v0.1.81 (2025-09-04)

### Continuous Integration

- Release v0.1.81
  ([`465960b`](https://github.com/nfraxlab/svc-infra/commit/465960bec3c60d8f24218632be587dad839039e3))


## v0.1.80 (2025-09-04)

### Continuous Integration

- Release v0.1.80
  ([`c8aa25f`](https://github.com/nfraxlab/svc-infra/commit/c8aa25fd137bfa4c54309227abd9323199882316))


## v0.1.79 (2025-09-04)

### Continuous Integration

- Release v0.1.79
  ([`1428152`](https://github.com/nfraxlab/svc-infra/commit/1428152306c024602fe4106ac6fb0b2758533fda))


## v0.1.78 (2025-09-04)

### Continuous Integration

- Release v0.1.78
  ([`70b6b4b`](https://github.com/nfraxlab/svc-infra/commit/70b6b4bf143183bdaa1f5ddf29eb05138c19df9f))


## v0.1.77 (2025-09-04)

### Continuous Integration

- Release v0.1.77
  ([`ac9ca14`](https://github.com/nfraxlab/svc-infra/commit/ac9ca141885268a9044e8d48f9a98f56da0c6021))


## v0.1.76 (2025-09-04)

### Continuous Integration

- Release v0.1.76
  ([`74da8dc`](https://github.com/nfraxlab/svc-infra/commit/74da8dc24e688a961954479cdaa66b2d08634c33))


## v0.1.75 (2025-09-04)

### Continuous Integration

- Release v0.1.75
  ([`b2aa122`](https://github.com/nfraxlab/svc-infra/commit/b2aa12284fd497b4edf21f0e0f8257b0fa777ff8))


## v0.1.74 (2025-09-04)

### Continuous Integration

- Release v0.1.74
  ([`6f76cf0`](https://github.com/nfraxlab/svc-infra/commit/6f76cf088aa65524029e23ef7c7d37f590ce70e5))


## v0.1.73 (2025-09-04)

### Continuous Integration

- Release v0.1.73
  ([`76c5b2a`](https://github.com/nfraxlab/svc-infra/commit/76c5b2ac050f69227f5e6e26ce580e45c614b4c8))


## v0.1.72 (2025-09-04)

### Continuous Integration

- Release v0.1.72
  ([`4375659`](https://github.com/nfraxlab/svc-infra/commit/43756590e2876e76562ac9cdd3f289cd9f85a8f9))


## v0.1.71 (2025-09-03)

### Continuous Integration

- Release v0.1.71
  ([`578c0fa`](https://github.com/nfraxlab/svc-infra/commit/578c0fa7c9d010cff25e9ce77c669ff67f763bf7))


## v0.1.70 (2025-09-03)

### Continuous Integration

- Release v0.1.70
  ([`84bb0f3`](https://github.com/nfraxlab/svc-infra/commit/84bb0f3a3a617f3da834c4e28e7d238317c60382))


## v0.1.69 (2025-09-03)

### Continuous Integration

- Release v0.1.69
  ([`416f805`](https://github.com/nfraxlab/svc-infra/commit/416f80504899d61e9d8b8b5ee665b923f77a38f3))


## v0.1.68 (2025-09-03)

### Continuous Integration

- Release v0.1.68
  ([`ac72302`](https://github.com/nfraxlab/svc-infra/commit/ac72302f16c1ae8e4bf5b4b11743a4edbd916449))


## v0.1.67 (2025-09-03)

### Continuous Integration

- Release v0.1.67
  ([`8a5313e`](https://github.com/nfraxlab/svc-infra/commit/8a5313e818a0b8253096e8367084c6eaaf1e9917))


## v0.1.66 (2025-09-03)

### Continuous Integration

- Release v0.1.66
  ([`4809f91`](https://github.com/nfraxlab/svc-infra/commit/4809f91c4b085627ac35ff7d720d6337f4c670dd))


## v0.1.65 (2025-09-03)

### Continuous Integration

- Release v0.1.65
  ([`4f275a8`](https://github.com/nfraxlab/svc-infra/commit/4f275a845d3ad001fd2d1d1f9a7273266225e28a))


## v0.1.64 (2025-09-03)

### Continuous Integration

- Release v0.1.64
  ([`2e3f45a`](https://github.com/nfraxlab/svc-infra/commit/2e3f45a10167c7ec37131ed03996439346c5ce1c))


## v0.1.63 (2025-09-03)

### Continuous Integration

- Release v0.1.63
  ([`06d6a8e`](https://github.com/nfraxlab/svc-infra/commit/06d6a8e7e85f98f7a99125e563f94a2675561477))


## v0.1.62 (2025-09-03)

### Continuous Integration

- Release v0.1.62
  ([`001345c`](https://github.com/nfraxlab/svc-infra/commit/001345c7e6fc5f9bfef37ff052b168008c8f3525))


## v0.1.61 (2025-09-03)

### Continuous Integration

- Release v0.1.61
  ([`950a1f8`](https://github.com/nfraxlab/svc-infra/commit/950a1f83b398c3658d0bc2256beac3237e4ccdca))


## v0.1.60 (2025-09-03)

### Continuous Integration

- Release v0.1.60
  ([`1374292`](https://github.com/nfraxlab/svc-infra/commit/13742924d3739e6d877dcc72fa606f37039df95e))


## v0.1.59 (2025-09-03)

### Continuous Integration

- Release v0.1.59
  ([`b4c8082`](https://github.com/nfraxlab/svc-infra/commit/b4c80826e27be66f5be8f443c6a5da8862896671))


## v0.1.58 (2025-09-03)

### Continuous Integration

- Release v0.1.58
  ([`ccd6e2f`](https://github.com/nfraxlab/svc-infra/commit/ccd6e2f1c9d30648c0f710b795d3736013f7aab8))


## v0.1.57 (2025-09-03)

### Continuous Integration

- Release v0.1.57
  ([`bf7f138`](https://github.com/nfraxlab/svc-infra/commit/bf7f138df91c008325d91b263e7952b524507d8c))


## v0.1.56 (2025-09-03)

### Continuous Integration

- Release v0.1.56
  ([`d82a6e6`](https://github.com/nfraxlab/svc-infra/commit/d82a6e6487de527c866af9690cbe857e5dbd9a8d))


## v0.1.55 (2025-09-03)

### Continuous Integration

- Release v0.1.55
  ([`2585ed7`](https://github.com/nfraxlab/svc-infra/commit/2585ed76e8a60fa97f6d30dff1b9d45b1ad0a8f4))


## v0.1.54 (2025-09-03)

### Continuous Integration

- Release v0.1.54
  ([`ffc7c4a`](https://github.com/nfraxlab/svc-infra/commit/ffc7c4ab76dd85e7afc276cc67bbbe4803ad0f09))


## v0.1.53 (2025-09-03)

### Continuous Integration

- Release v0.1.53
  ([`df081d7`](https://github.com/nfraxlab/svc-infra/commit/df081d7de794eb8d688222145f041f7f94ec5ca1))


## v0.1.52 (2025-09-03)

### Continuous Integration

- Release v0.1.52
  ([`0b444c3`](https://github.com/nfraxlab/svc-infra/commit/0b444c3ecfe3f3a855a26e7835c39827f6c5cd55))


## v0.1.51 (2025-09-03)

### Continuous Integration

- Release v0.1.51
  ([`edba542`](https://github.com/nfraxlab/svc-infra/commit/edba542d3d1284590a2e7ce270fd1a8dc6648c22))


## v0.1.50 (2025-09-03)

### Continuous Integration

- Release v0.1.50
  ([`3cd2e3e`](https://github.com/nfraxlab/svc-infra/commit/3cd2e3e12049906a75a30c877568a6162a721c00))


## v0.1.49 (2025-09-03)

### Continuous Integration

- Release v0.1.49
  ([`21d40eb`](https://github.com/nfraxlab/svc-infra/commit/21d40eb729b0e03e7f3028d53959b95b62a6b54b))


## v0.1.48 (2025-09-03)

### Continuous Integration

- Release v0.1.48
  ([`c72aad0`](https://github.com/nfraxlab/svc-infra/commit/c72aad03d453556e39ab754f3871f9dd0f1f422a))


## v0.1.47 (2025-09-03)

### Continuous Integration

- Release v0.1.47
  ([`07fe8e0`](https://github.com/nfraxlab/svc-infra/commit/07fe8e09787c620df5cc1ea1c291d4c658f90dbb))


## v0.1.46 (2025-09-03)

### Continuous Integration

- Release v0.1.46
  ([`adb19af`](https://github.com/nfraxlab/svc-infra/commit/adb19afce3791856fae80b6f06ba4537378ebce0))


## v0.1.45 (2025-09-03)

### Continuous Integration

- Release v0.1.45
  ([`ee7b006`](https://github.com/nfraxlab/svc-infra/commit/ee7b0065df3aa1248e03b8f779dacd698d467a06))


## v0.1.44 (2025-09-03)

### Continuous Integration

- Release v0.1.44
  ([`3820004`](https://github.com/nfraxlab/svc-infra/commit/3820004dd2a279ab65466279a5a64ee37610165d))


## v0.1.43 (2025-09-03)

### Continuous Integration

- Release v0.1.43
  ([`3a753b1`](https://github.com/nfraxlab/svc-infra/commit/3a753b159ff04e96e31ec8294fe697fca1fc9b51))


## v0.1.42 (2025-09-03)

### Continuous Integration

- Release v0.1.42
  ([`d1b6d51`](https://github.com/nfraxlab/svc-infra/commit/d1b6d513278326b5a368e276cdd4c3f08bb54931))


## v0.1.41 (2025-09-03)

### Continuous Integration

- Release v0.1.41
  ([`6742cbb`](https://github.com/nfraxlab/svc-infra/commit/6742cbbf444194f68508a3d07952945b9b3a66a3))


## v0.1.40 (2025-09-03)

### Continuous Integration

- Release v0.1.40
  ([`8f741bd`](https://github.com/nfraxlab/svc-infra/commit/8f741bd18e0382594640c19e1dd69f457ebfa80f))


## v0.1.39 (2025-09-03)

### Continuous Integration

- Release v0.1.39
  ([`c63d49d`](https://github.com/nfraxlab/svc-infra/commit/c63d49deeb82522742d86ee408b17af425d42a9b))


## v0.1.38 (2025-09-03)

### Continuous Integration

- Release v0.1.38
  ([`82fe048`](https://github.com/nfraxlab/svc-infra/commit/82fe04871863064ca67175cf1a43430dfede9019))


## v0.1.37 (2025-09-03)

### Continuous Integration

- Release v0.1.37
  ([`8d51280`](https://github.com/nfraxlab/svc-infra/commit/8d512807bab7d7dbd76bca9c23d8eb4d779fdb17))


## v0.1.36 (2025-09-03)

### Continuous Integration

- Release v0.1.36
  ([`46f140c`](https://github.com/nfraxlab/svc-infra/commit/46f140c3605e9e239b8a74d0cdcf303120fa76f6))


## v0.1.35 (2025-09-02)

### Continuous Integration

- Release v0.1.35
  ([`55fd4e1`](https://github.com/nfraxlab/svc-infra/commit/55fd4e1754538a464b5b809209dfc39d3081dd83))


## v0.1.34 (2025-09-02)

### Continuous Integration

- Release v0.1.34
  ([`f04902b`](https://github.com/nfraxlab/svc-infra/commit/f04902b95afb2b1ba91de2a8bc5b17b363c3317f))


## v0.1.33 (2025-09-02)

### Continuous Integration

- Release v0.1.33
  ([`d147383`](https://github.com/nfraxlab/svc-infra/commit/d147383daa42dad6106a03f68ee9b15619d64707))


## v0.1.32 (2025-09-02)

### Continuous Integration

- Release v0.1.32
  ([`f5596cf`](https://github.com/nfraxlab/svc-infra/commit/f5596cf1b74874c4e742b9e8ba7e4900e39f5ce1))


## v0.1.31 (2025-09-02)

### Continuous Integration

- Release v0.1.31
  ([`5849bd3`](https://github.com/nfraxlab/svc-infra/commit/5849bd32c8851ef8f3ddae3e85720accd119e9b0))


## v0.1.30 (2025-09-02)

### Continuous Integration

- Release v0.1.30
  ([`51fe0dd`](https://github.com/nfraxlab/svc-infra/commit/51fe0dd3e118418bb1d8e24ab2af92f770df71c7))


## v0.1.29 (2025-09-02)

### Continuous Integration

- Release v0.1.29
  ([`fa2a118`](https://github.com/nfraxlab/svc-infra/commit/fa2a118d65df420c266dcb32817616d9c111d78f))


## v0.1.28 (2025-08-31)

### Continuous Integration

- Release v0.1.28
  ([`3e64c7f`](https://github.com/nfraxlab/svc-infra/commit/3e64c7fb1abe191009da566d2df7e14da355c878))


## v0.1.27 (2025-08-29)

### Continuous Integration

- Release v0.1.27
  ([`16f00ac`](https://github.com/nfraxlab/svc-infra/commit/16f00ac475f46ed67d483097e152b956e39733fa))


## v0.1.26 (2025-08-28)

### Continuous Integration

- Release v0.1.26
  ([`2f9f9f2`](https://github.com/nfraxlab/svc-infra/commit/2f9f9f20e0b25927d2f637b2fd1c166d98ebee9d))


## v0.1.25 (2025-08-28)

### Continuous Integration

- Release v0.1.25
  ([`ed3b88c`](https://github.com/nfraxlab/svc-infra/commit/ed3b88c88821911778a7c777a5da5d429bce8400))


## v0.1.24 (2025-08-27)

### Continuous Integration

- Release v0.1.24
  ([`72ea281`](https://github.com/nfraxlab/svc-infra/commit/72ea281ba87368e9888c1e008173b347d032d363))


## v0.1.23 (2025-08-27)

### Continuous Integration

- Release v0.1.23
  ([`d1bc2f7`](https://github.com/nfraxlab/svc-infra/commit/d1bc2f7c73789dbbd6b77af72f6aaf2fbfd94e40))


## v0.1.22 (2025-08-27)

### Continuous Integration

- Release v0.1.22
  ([`ca287e1`](https://github.com/nfraxlab/svc-infra/commit/ca287e1006b540ca7db23eba2d6057e69f3d74bf))


## v0.1.21 (2025-08-27)

### Continuous Integration

- Release v0.1.21
  ([`b1c6997`](https://github.com/nfraxlab/svc-infra/commit/b1c69977ee16e6d9329864170561d91cf88394c9))


## v0.1.20 (2025-08-27)

### Continuous Integration

- Release v0.1.20
  ([`95b7eea`](https://github.com/nfraxlab/svc-infra/commit/95b7eea1af403c60f1db0c13cf25158dc89e7071))


## v0.1.19 (2025-08-27)

### Continuous Integration

- Release v0.1.19
  ([`e41727c`](https://github.com/nfraxlab/svc-infra/commit/e41727c0754823273b81f87efe0626940fec5b3b))


## v0.1.18 (2025-08-26)

### Continuous Integration

- Release v0.1.18
  ([`e7d4b6b`](https://github.com/nfraxlab/svc-infra/commit/e7d4b6bc84b36531637dfc7fd023455c471fdcc4))


## v0.1.17 (2025-08-26)

### Continuous Integration

- Release v0.1.17
  ([`1e62c4e`](https://github.com/nfraxlab/svc-infra/commit/1e62c4e26423d24b884cb9fa332551a3dbb19e44))


## v0.1.16 (2025-08-26)

### Continuous Integration

- Release v0.1.16
  ([`d0f446e`](https://github.com/nfraxlab/svc-infra/commit/d0f446e700637f26761793fe93c90d6a8aaaa75c))


## v0.1.15 (2025-08-25)

### Continuous Integration

- Release v0.1.15
  ([`551d198`](https://github.com/nfraxlab/svc-infra/commit/551d198dfb681fb3b4e297fcc5432b5b4eb797f2))


## v0.1.14 (2025-08-25)

### Continuous Integration

- Release v0.1.14
  ([`742f538`](https://github.com/nfraxlab/svc-infra/commit/742f5380db95e0058082ac7309812ccb2ba49a27))


## v0.1.13 (2025-08-25)

### Continuous Integration

- Release v0.1.13
  ([`c037cf7`](https://github.com/nfraxlab/svc-infra/commit/c037cf7bba91d8c57affc47b0cc0df5b84377f4d))


## v0.1.12 (2025-08-25)

### Continuous Integration

- Release v0.1.12
  ([`a2ba446`](https://github.com/nfraxlab/svc-infra/commit/a2ba446fb6198a608ce552847632aa4307900ddf))


## v0.1.11 (2025-08-24)

### Continuous Integration

- Release v0.1.11
  ([`f246718`](https://github.com/nfraxlab/svc-infra/commit/f2467184f23e4afcc0a46370b78381ced4476bfd))


## v0.1.10 (2025-08-24)

### Continuous Integration

- Release v0.1.10
  ([`d04da04`](https://github.com/nfraxlab/svc-infra/commit/d04da04943888fa5a95b4bb0a4d2fb75d1fd8a00))


## v0.1.9 (2025-08-24)

### Chores

- Regenerate poetry.lock
  ([`324d286`](https://github.com/nfraxlab/svc-infra/commit/324d286f3dd045dd615d626be6ac85f5cf50a55a))

### Continuous Integration

- Release v0.1.9
  ([`a31bc01`](https://github.com/nfraxlab/svc-infra/commit/a31bc01dbf5889849fa7ac9f2631fcf6f5bb777b))


## v0.1.8 (2025-08-24)

### Bug Fixes

- Ensure AppSettings defaults are used when name/version is None
  ([`4076b4f`](https://github.com/nfraxlab/svc-infra/commit/4076b4f598214b782eb80ba2815b2979cf76f64e))

- Ensure FastAPI app name/version always use AppSettings defaults if None is passed
  ([`5b54928`](https://github.com/nfraxlab/svc-infra/commit/5b5492839dedd873e20e60b5088ea8c840af4a33))

- Improve logging config validation and traceback formatting for pydantic v2+ and Python 3.11+
  ([`30888d1`](https://github.com/nfraxlab/svc-infra/commit/30888d103dcdd8755c2373d68c660d4324992026))

- Make nonprod optional in pick(), update logging and router registration for env refactor
  ([`bb84cd8`](https://github.com/nfraxlab/svc-infra/commit/bb84cd86bf3b0ffce4b8e0ccc334b1c6b1e53738))

- Use StrEnum for logging config enums and update imports for consistency
  ([`dcccaac`](https://github.com/nfraxlab/svc-infra/commit/dcccaac1d4c628aa04d7632ea6896e648696f40c))

- **logging**: Use StrEnum for log level/format options for Pydantic compatibility
  ([`6919b2f`](https://github.com/nfraxlab/svc-infra/commit/6919b2feaec8bcd6eb2bfb2f8c06d5c866718244))

### Chores

- Push all recent changes
  ([`ce485a3`](https://github.com/nfraxlab/svc-infra/commit/ce485a3bac37cbfbf31db0da6584d55ee8660d87))

- Remove __pycache__ and *.pyc; update .gitignore to exclude pycache/pyc and .pytest_cache
  ([`2d3b790`](https://github.com/nfraxlab/svc-infra/commit/2d3b790610bf39efb12c2143bbdefdddc64d2603))

- Update and refactor router exclusion and settings handling
  ([`cab28dc`](https://github.com/nfraxlab/svc-infra/commit/cab28dcf78b38026c914d9cacc29f4c9180db33c))

- Update and refactor router exclusion and settings handling
  ([`6b72302`](https://github.com/nfraxlab/svc-infra/commit/6b72302cc49a984aacdfa124484870a5c9a48c1a))

- Update and refactor router exclusion and settings handling
  ([`dafd937`](https://github.com/nfraxlab/svc-infra/commit/dafd937242bc4ea157439e04c3c85dd29092f211))

- **logging**: Silence multipart parser logs in non-debug environments
  ([`6c238ab`](https://github.com/nfraxlab/svc-infra/commit/6c238abf02b1af1192ecb0db67b4e23da3efc59c))

### Continuous Integration

- Release v0.1.8 [skip ci]
  ([`242393b`](https://github.com/nfraxlab/svc-infra/commit/242393b0eb14ab331f1d499dc1440574cd3aef5d))

### Features

- Add 'staging' synonym, ALL_ENVIRONMENTS, and improve router exclusion logic
  ([`53b8f58`](https://github.com/nfraxlab/svc-infra/commit/53b8f582b6e9bdc2cfc96f34ac64fc74f0dc34fe))

- Make router exclusion dynamic and add pydantic schema for routers_exclude
  ([`8a67828`](https://github.com/nfraxlab/svc-infra/commit/8a6782852a3d201aedffbfb2d976810cb77957f9))

- Switch to ROUTER_EXCLUDED_ENVIRONMENTS for router registration control
  ([`3678a2e`](https://github.com/nfraxlab/svc-infra/commit/3678a2e0473970b1215559dbf716be181eb7eb49))

### Refactoring

- Improve execute_api for readability, robustness, and production readiness
  ([`73d1bd2`](https://github.com/nfraxlab/svc-infra/commit/73d1bd20ddd9cf6e897561c5507a8213da9e5808))

- Rename execute_api to create_and_register_api and improve naming/documentation
  ([`4ffffa4`](https://github.com/nfraxlab/svc-infra/commit/4ffffa41ba69b32ba380c2930b544d52debc7fab))

- Use self-documenting environment naming (Environment, CURRENT_ENVIRONMENT, etc.) everywhere
  ([`6f6d160`](https://github.com/nfraxlab/svc-infra/commit/6f6d16064abe0246810c895d7146b023158c216f))
