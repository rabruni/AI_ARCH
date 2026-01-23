# repo_os — Module Standard

## Purpose
This module is a self-contained, declarative operating system for repositories.

## Structural Invariants
- All operational assets live under this module directory
- This module exposes a control plane via registries
- No hidden or implicit behavior is allowed

## Standards Followed
- **GitOps** — ArgoCD / declarative desired state / PR as change gate
- **Infrastructure as Code** — Terraform/CDK principles applied to repos
- **CNCF Configuration Best Practices** — Separation of config, code, and state
- **OWASP ASVS** — Secure-by-default repo and CI practices
- **Semantic Versioning** — MAJOR/MINOR/PATCH for registries and prompts
- **Unix Philosophy** — Small, composable, inspectable tools

## Enforcement
- Registry-driven desired state
- CI validation required
- Deterministic regeneration must be possible

## Prohibited
- Manual state
- Undeclared artifacts
- Cross-module coupling
