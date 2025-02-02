/label ~"meta: release"

1. [x] create a release issue (title: 'x.x.x release', milestone: x.x.x)
1. [ ] create merge request from release issue
1. [ ] bump Python package version: `scripts/release {major/minor/patch}`
1. [ ] push changes, merge into `main` and tag commit with version
1. [ ] clean up prerelease virtual environments `docs/deploy.md#clean-prerelease-virtual-environments`
