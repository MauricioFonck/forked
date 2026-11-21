# 10. Open-Source Governance and Contribution Model

## 10.1 Proposed licensing
- Software: Apache License 2.0.
- Documentation: CC BY 4.0.
- Benchmark fixtures: document each dataset's license and provenance.
- Protocol specification: openly available; select a permissive specification license after legal review.

Confirm all dependency licenses and third-party assets before distribution.

## 10.2 Contribution workflow
- Issues describe problem, context, expected behavior, and acceptance criteria.
- Pull requests include tests and docs.
- Security-sensitive reports use private disclosure.
- Maintainers review API/schema changes carefully.
- Breaking protocol changes require a design proposal and migration plan.

## 10.3 Required repository policies
- `CODE_OF_CONDUCT.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `GOVERNANCE.md`
- `CITATION.cff`
- issue and PR templates
- changelog and release process
- dependency update automation

## 10.4 Decision process
For early stage:
- project lead maintains scope and release coordination;
- technical decisions documented as ADRs;
- external contributors can propose changes;
- no claim of community governance until maintainers and processes exist.

As the project grows:
- establish maintainer roles;
- publish decision criteria;
- consider a technical steering group;
- explore neutral stewardship only after demonstrated independent adoption.

## 10.5 Community principles
- welcoming and respectful participation;
- credit contributors;
- avoid vanity metrics and artificial stars;
- transparent roadmap;
- reproducible bug reports;
- clear distinction between proposal, implementation, and validated result.
