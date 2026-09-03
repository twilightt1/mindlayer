# OSS Growth Playbook — What Actually Grows Self-Hosted Open-Source Projects from 0 → Thousands of Stars and Dozens of Contributors

**Date:** 2026-09-02
**Prepared for:** Orivory (MIT-licensed, self-hosted AI second brain; FastAPI + Next.js; solo maintainer; pre-launch MVP)
**Research question:** What demonstrably grows open-source developer/self-hosted projects from 0 to thousands of stars and dozens of active contributors — with evidence?

## Method note

Desk research conducted 2026-09-02 via web search and primary-source reading. Every claim carries an inline source URL. Evidence quality varies and is labeled:

- **[Study]** = peer-reviewed or large-scale empirical research (arXiv, ACM, IEEE, NSF-par).
- **[Primary]** = first-party source (project blog, GitHub repo/discussion, official docs, standards RFC).
- **[Secondary]** = journalism, podcast write-ups, third-party trackers. Numbers from third-party trackers (Discord member counts, star counts) are snapshots and approximate.
- Star/contributor counts are **"as of" the cited snapshot date** and change continuously.
- Where evidence was searched for but **not found**, this is stated honestly in the section ("gap") rather than filled with speculation.

---

## 1. Contributor growth mechanics that demonstrably work

### 1.1 Why newcomers fail (the baseline problem)

- The canonical systematic literature review (20 primary studies) identified **15 barriers in 5 categories** (social interaction, previous knowledge, finding a way to start, documentation, technical hurdles). Social-interaction barriers were the most evidenced — appearing in **15 of 20 studies (75%)**, mostly around not receiving timely/proper answers. **[Study]** — Steinmacher et al., *Information and Software Technology* 59 (2015): https://dl.acm.org/doi/10.1016/j.infsof.2014.11.001 (open preprint: https://www.ime.usp.br/~gerosa/papers/IST_SysReview_PrePrint.pdf)
- Practical implication for a small project: **responsiveness beats polish**. The two cheapest levers are (a) fast, kind answers and (b) removing setup friction.

### 1.2 CONTRIBUTING.md — real but nuanced evidence

- **Temporal association study (2025):** adding and then *maintaining* a CONTRIBUTING.md measurably improved first-time-PR acceptance. In the analyzed projects, first-pull acceptance rose **51% → 64% after inserting** the file and **64% → 95% after updating** it; in another example, **62% → 83% → 90%** after two revisions. **[Study]** — Gonçalves, Plastino & Soares, SEMISH 2025: https://doi.org/10.5753/semish.2025.6870
- **Coverage gap study:** most CONTRIBUTING files fail newcomers. In a sample of 2,274 GitHub projects, **~65% had no CONTRIBUTING file at all**; of those that did, **84% missed ≥2 of 6** newcomer-barrier categories and **52% missed ≥3**. Only **23%** explained *how to choose a task* and **28%** *how to build the local workspace* — the two barriers newcomers hit first. **[Study]** — Fronchetti et al., *"Do CONTRIBUTING Files Provide Information about OSS Newcomers' Onboarding Barriers?"*: https://par.nsf.gov/servlets/purl/10493930
- **Counter-evidence to keep in view:** a large Debian-based study found projects typically publish CONTRIBUTING files **~1,806 days (≈5 years) in**, *after* a flurry of contributions, and found **no causal evidence** that the file itself catalyzes growth; it also found some content types (installation/configuration instructions; code-style guidance) were associated with more subsequent activity. **[Study]** — Gaughan, Champion, Hwang & Shaw (2025): https://arxiv.org/pdf/2502.18440
- **Signals study (9,977 GitHub projects):** in interviews, contributors called contributing guidelines a *decisive* signal — "lacking one would induce an immediate negative impression" — but the quantitative regression surprisingly showed a **negative association** between merely having a CONTRIBUTING file and attracting new contributors (likely confounded: older, established projects have both). The actionable part: guidelines must be **prominent (linked in README), thorough, and not overly process-heavy**. **[Study]** — Qiu et al., CSCW 2019: https://cmustrudel.github.io/papers/cscw19signals.pdf
- **Verdict:** a CONTRIBUTING.md is cheap insurance with the best documented *within-project* effect (acceptance-rate lift), but only if it covers **task selection + workspace setup + how to get a response**, and is linked from the README.

### 1.3 `good first issue` labels — the single strongest documented lever

- Working on a GFI-labeled task gave newcomers **5.57× higher odds** of first-patch acceptance on GitHub projects (bug-fix PRs: **2.41×** odds vs. other change types on Android/gerrit projects; smaller diffs also accepted more). **[Study]** — Turzo, Sultana & Bosu (2024): https://doi.org/10.48550/arxiv.2407.04159
- Large-scale GFI study (48,402 GFI-closed issues across 964 repos): **~70% of GFIs had expert participation**, and half received a first expert comment **within 8.5 hours** of a newcomer comment. Expert involvement **positively correlates with successful contribution but negatively with newcomer retention** (i.e., hand-holding ships the PR but doesn't keep people by itself). **[Study]** — ICSE 2023, *"Is it Enough to Recommend Tasks to Newcomers?"*: https://dl.acm.org/doi/10.1109/ICSE48619.2023.00064
- Practice at scale: Cal.com staffed a dedicated **"Community Team" whose explicit job is quickly reviewing community PRs and shepherding them to merge** ("Ensures our open source contributors have a great experience"), and reported that most of its engineers **started as project contributors** — a contributor→hire pipeline. **[Primary]** — https://cal.com/blog/engineering-in-2026-and-beyond ; https://cal.com/blog/series-a-memo ; https://cal.com/blog/open-source
- **Gap:** I did not find a published before/after study of any specific "greetings bot" (welcome-bot, first-timers-bot) showing contributor-count lift. Treat bots as triage helpers, not evidence-backed growth mechanics. Stale-bot style automation is widely used but its effect on contributor retention is unstudied in what I found.

### 1.4 One-command / zero-setup contributor environments

- Dev Containers + GitHub Codespaces case study (OpenFeature .NET SDK maintainers): a single `.devcontainer/devcontainer.json` "codified build tools, base images, extensions — every Codespace runs identically," explicitly recommended **measuring time-to-first-PR** as the success metric; they observed lower "support" time untangling setup issues. **[Secondary/primary-adjacent]** — https://medium.com/@askpt/dev-containers-removing-friction-to-accelerate-contributor-onboarding-391c09ccfbb2 ; GitHub's own docs on devcontainer configurations: https://docs.github.com/en/codespaces/setting-up-your-project-for-codespaces/adding-a-dev-container-configuration/introduction-to-dev-containers
- Practitioner report: a contributor who "normally wouldn't have been able to test this locally on my Windows setup" submitted a security-relevant PR *because* the repo had a devcontainer; setup cost for the maintainer ≈ **20 minutes**; Codespaces free tier is 120 core-hours/month, enough for casual contributors. **[Secondary]** — https://iamanuragh.in/blog/2026-03-02-github-codespaces-zero-setup-open-source-contributions/
- This directly attacks the two worst-covered CONTRIBUTING barriers (workspace setup: 28% coverage; task selection: 23%) — see 1.2. **[Study]** — https://par.nsf.gov/servlets/purl/10493930
- For a self-hosted app (Orivory's shape), the equivalent is a `docker compose` dev stack with **seeded fake data** plus a devcontainer — the same one-command philosophy, applied to a two-process (API+web) system.

### 1.5 Recognition: all-contributors

- The all-contributors spec (recognizing non-code contributions — docs, design, triage, translation — with emoji keys in the README) reports **2,000+ projects using it**, with a bot that automates README updates. **[Primary]** — https://allcontributors.org/en/ ; bot repo: https://github.com/all-contributors/all-contributors-bot
- No independent study of its effect on retention was found; it is best understood as a cheap, honest recognition surface for the ~60% of contributors who never touch code (mirroring the GitHub-survey finding that most people don't contribute docs even though everyone reads them — see §5).

### 1.6 RFC / proposal processes — you are not there yet (and shouldn't be)

- Rust's RFC process (RFCs for "substantial" changes; shepherd assigned; **10-day Final Comment Period**; sub-team sign-off) exists because Rust needed "a consistent and controlled path" once it matured — and its own governance RFC admits the process became **"a victim of its own success":** volume outgrew the core team, shepherds couldn't keep up, and the process "started to feel heavyweight (especially for newcomers)," requiring sub-teams to scale. **[Primary]** — https://rust-lang.github.io/rfcs/ ; RFC 1068 governance text: https://github.com/rust-lang/rfcs/blob/HEAD/text/1068-rust-governance.md ; lang-team guidance that small uncontroversial changes skip RFCs entirely: https://lang-team.rust-lang.org/how_to/propose.html
- Python's PEP process likewise requires a **sponsor/core developer** to champion a PEP, PEP editors, and ultimately the Steering Council for acceptance — machinery for a project with hundreds of contributors. **[Primary]** — https://peps.python.org/pep-0001/
- **Implication:** at MVP/solo scale, an RFC process is negative-impact (process theater that deters exactly the people you want). What mature projects teach you to adopt *early* instead: a lightweight "ask first before building big features" note in CONTRIBUTING (the "please ask first" pattern contributors explicitly valued — Qiu et al., §1.2), and an issue template that captures the problem before the PR.

---

## 2. Bounties: Algora, Polar, Gitcoin-style

### 2.1 What the platforms actually moved (numbers)

- **Algora (platform-wide, at launch, Sept 2023):** OSS projects on the platform had awarded **$65,785 across 600 bounties to 188 contributors from 48 countries**, with 43 projects posting 242 open bounties ($46,899) at that time. **[Primary]** — Algora founder's post: https://medium.com/@giannis_34055/algora-open-source-coding-bounties-5083edc5327f ; Show-HN thread (same numbers): https://news.ycombinator.com/item?id=37769595
- **Largest single funder (2026 audit):** tscircuit — **707 completed bounties** — but its open-bounty board showed a **$341 issue with 236 claims still open after 21 months**; fresh Algora bounties reportedly attract **8–158 attempts within hours**. **[Secondary]** — https://dev.to/aion_autonomous_org/i-measured-the-open-source-bounty-market-before-entering-it-then-i-didnt-enter-93n ; market survey table: https://dev.to/zeroknowledge0x/the-open-source-money-map-every-way-developers-are-actually-making-money-in-2026-with-real-45ba
- **Polar, maintainer-side experiment (real numbers):** Polar's own developer support created an examples repository and awarded **32 bounties totaling $2,625** (mostly $25–$200 for SDK examples and docs), and described the hard parts honestly: "explaining the exact ask… make sure nobody overturns/copies an existing PR, make sure someone has actually put in the effort (vs generate them blindly with AI)." **[Primary]** — https://rishi.app/blog/polar
- **Polar explicitly rejects the bounty model for its core product:** "We designed issue funding for maintainers & contributors vs. bounty hunters. **We don't believe in traditional bounties**" — and takes a **10% commission** on funded issues (maintainer keeps 90%). **[Primary]** — https://news.ycombinator.com/item?id=39382281 ; https://polar.sh/polarsource/posts/introducing-rewards ; https://polar.sh/polarsource/posts/polar-v1-0-lets-fix-open-source-funding
- Repos using Algora for specific work: Twenty posted e.g. a **$2,500 IMAP-support bounty**; tscircuit routinely funds $100–$300 issues. **[Secondary]** — https://dev.to/tatelyman/how-i-earn-money-from-open-source-bounties-on-algora-f5e

### 2.2 Does Algora actually move contributor counts?

- **Verdict: it reliably moves *attempts*, not reliably *reviewable contributors*.** The scarce resource is maintainer review time, not money: "Adding funding to that issue five separate times didn't close it… AI made attempting a bounty nearly free, while reviewing still costs the maintainer what it always did." **[Secondary]** — https://dev.to/aion_autonomous_org/i-measured-the-open-source-bounty-market-before-entering-it-then-i-didnt-enter-93n
- A bug-bounty-adjacent empirical study (OSS security bounties via huntr; 51 listings / 90 surveys / 17 interviews) found the same pattern from the maintainer side: **low-quality or spam reports were the most-listed challenge**, and "hunters focused on money or CVEs" was ranked the most difficult aspect of review. **[Study]** — https://arxiv.org/html/2409.07670v1
- Positive framing that is supportable: a bounty program is a **contributor-acquisition and company-alignment tool**, not a growth strategy — best used for small, precisely-scoped tasks *after* you have review capacity, ideally on docs/examples/translators where "good enough" is verifiable cheaply (exactly where Polar's 32-for-$2,625 experiment landed). **[Primary]** — https://rishi.app/blog/polar
- **Gap:** I found no repo publishing a clean before/after *contributor-count* series attributable to bounties alone. Anyone claiming "bounties grew us from X to Y contributors" in what I found is conflating star growth and marketing with bounty effects.

### 2.3 Gitcoin-style (crypto) models

- Not researched in depth here (orthogonal to a solo MIT dev-tool project); the maintainer-side findings from huntr/Algora/Polar above are the transferable evidence.

---

## 3. Community infrastructure: Discord, Matrix, Discussions, Hacktoberfest

### 3.1 Sizes and channel strategies of comparable self-hosted projects

| Project | Primary chat | Size (snapshot) | Source |
|---|---|---|---|
| Home Assistant | Discord (+ big forum) | **~163,346 Discord members** (third-party tracker); r/HomeAssistant ≈ 574K | [Secondary tracker] https://disdex.io/server/330944238910963714 ; https://thehiveindex.com/communities/r-homeassistant/ |
| Immich | Discord (+ Reddit) | **39,609 members, 5,353 online** (official server listing); r/immich ≈ 61K (+29K in ~a year) | [Primary listing] https://discord.com/servers/immich-979116623879368755 ; [Secondary] https://gummysearch.com/r/immich/ |
| Jellyfin | **Matrix-first** (#jellyfin:matrix.org) | **16,401 members** in general room; 1,674 lifetime contributors (OpenHub) | https://matrixrooms.info/room/jellyfin:matrix.org ; https://openhub.net/p/jellyfin |
| Paperless-ngx | **Matrix + GitHub Discussions** (deliberately non-Discord) | "Community support is available via GitHub Discussions and the Matrix chat room" (official docs) | [Primary] https://docs.paperless-ngx.com/ ; https://github.com/paperless-ngx/paperless-ngx |

- **The documented failure mode of huge Discords:** Home Assistant's own community team writes that in a server of "tens of thousands (let alone over 100,000)" support in chat "can be overwhelming or simply useless… your message is lost." Their mitigations: **role-gated developer channels** (self-selected role via onboarding questions) and structured join-time role selection so newcomers can't flood dev channels. Meanwhile the forum's stats thread documents the flip side: conversations moving into Discord made knowledge **harder to find** ("Discord… is not indexable"), hurting the searchable forum. **[Primary]** — https://community.home-assistant.io/t/discord-changes-are-now-live/771238 ; https://community.home-assistant.io/t/forum-stats/1005831
- **Pattern to copy:** Paperless-ngx and Jellyfin keep support **searchable and indexable** (GitHub Discussions / Matrix archives) and organize contributors into named teams (Paperless-ngx: frontend, ci/cd, etc.; Jellyfin: a written constitution with leadership team, subproject leaders, and contributor function teams — https://github.com/jellyfin/jellyfin-meta/blob/master/policies-and-procedures/jellyfin-constitution.md ). Jellyfin chose Matrix over Discord/Slack explicitly because those are "not indexable and siloed by a private company" (community takeover discussion): https://github.com/jonaswinkler/paperless-ng/issues/1599
- **Implication for a 0→1k project:** one chat (Discord is where self-hosters are; Matrix where the values are) **plus** GitHub Discussions as the searchable support archive beats either alone. The chat is for responsiveness (the #1 newcomer barrier, §1.1); Discussions are for knowledge retention.

### 3.2 Community calls / office hours / sprints

- **Honest gap:** I did not find quantitative evidence that community calls or "office hours" measurably move contributor counts for projects at Orivory's scale. What exists: commercial-OSS community talks describing structured contributor programs (e.g., Formbricks' OCS 2023 talk on gamified onboarding — https://www.coss.community/cossc/ocs-2023-johannes-dancker-formbricks-161c ). Treat monthly calls as cheap culture, not a proven lever.

### 3.3 Hacktoberfest: documented quality criticism

- The canonical maintainer account (whatwg/html maintainer Domenic Denicola, Sept 30, 2020): closing **11 spam PRs in one day**, a rate of **~4 spam PRs/hour**, each generating notifications to **485 watchers** and requiring manual close→tag-spam→lock→report; DigitalOcean's own 2019 metrics showed **3,712 PRs labeled spam** by maintainers; he calls Hacktoberfest "a corporate-sponsored distributed denial of service attack against the open source maintainer community." **[Primary blogpost]** — https://domenic.me/hacktoberfest/
- Coverage: InfoQ (https://www.infoq.com/news/2020/10/hacked-off-hacktoberfest/), Changelog (https://changelog.com/news/hacktoberfest-is-hurting-open-source-nL90), a documented spam archive (https://github.com/shitoberfest/spam-pullrequests).
- Balanced empirical note (Veracode analysis): Hacktoberfest "did seem to accomplish its top-line objective: …large amounts of users suddenly committed code" — the problem is gamified low-quality volume, spread via YouTube "how to game it" videos. **[Secondary]** — https://www.veracode.com/blog/spooky-occurrence-open-source-hacktoberfest-2020/
- The fix that worked: DigitalOcean made participation **opt-in per repository** (repo-maintainer change documented in the swag-list maintainer's issue; spam "measurably" dropped after opt-in went live) — https://github.com/crweiner/hacktoberfest-swag-list/issues/305
- **Implication:** if you ever opt in, do it *only* with a maintained, well-labeled issue board and explicit review-time budget; the default is maintainers absorbing spam cost.

---

## 4. Solo-maintainer → community transitions (documented stories, with numbers)

### 4.1 Immich — Alex Tran (the transparency-cadence story)

- Origin: built for his wife's Google-Photos problem; **posted a prototype video to r/selfhosted** and the project took off from Reddit. **[Primary interview]** — https://share.snipd.com/episode/b8b1cd75-965e-49b8-a0e0-000000000000 (Self-Host Cast ep. 4: https://selfh.st/cast/episode-4/)
- 2024 year-in-review (first-person, with numbers): **+30k GitHub stars added in 2024** (23,940 on Jan 16, 2024); **900+ community contributors**; switch **MIT → AGPLv3** (to keep hosted forks honest — full rationale discussion: https://github.com/immich-app/immich/discussions/7023); funded full-time by **FUTO** (nonprofit) with no paywalled features; Alex kept a **150-day Reddit comment streak** — responsiveness as a personal practice. **[Primary]** — https://immich.app/blog/2024-year-in-review
- The famous trust artifact: the README warning — *"Project is under very active development. Expect bugs and changes. **Do not use it as the only way to store your photos and videos!**"* — honest expectation-setting repeatedly cited as a trust builder. **[Secondary analysis]** — https://medium.com/@Emily_OnChain/immich-an-open-source-devrel-case-study-57747bb5e5d2
- Two-year FUTO retrospective: team grew to **~10 people**, product-key monetization, first paid intern, Alex still BDFL; the team explicitly answered the community's 6 skepticism points in public. **[Primary]** — https://immich.app/blog/futo-two-years-later
- **What mattered in year one:** relentless public responsiveness (Reddit/GitHub/Discord), honest instability warnings, detailed changelogs, and a funding moment announced transparently with community concerns addressed in public.

### 4.2 Dokploy — Mauricio Siu (fastest solo→community case, and its cautionary lesson)

- <2 years from first commit (repo created 2024-04-19): **30,000 stars, 270 contributors, 5,200 commits, 140+ releases, 6M Docker Hub downloads, 2,000+ forks**; repo now ~36.7k stars with the founder at 4,547 contributions (#2 is a CI bot at 244). **[Primary LinkedIn + repo]** — https://www.linkedin.com/posts/carlos-mauricio-ortiz-siu-6b9011184_dokploy-just-hit-30000-stars-on-github-activity-7426526878410375168-NhOJ ; https://github.com/dokploy/dokploy
- The cautionary lesson (maintainer's own admission + community review): after 2 years solo, Dokploy had **~500 open issues, 180+ open PRs**, and a contributor scored the PR-feedback loop **"approximately 10 out of 100"** — "Months of silence leave people unable to improve their work… Several people… stopped contributing because of the lack of feedback." The community's fix list is effectively a free playbook: **(1)** acknowledge every new PR within 7 days even without a full review; **(2)** publish a scope doc ("what Dokploy is and isn't"); **(3)** public roadmap on GitHub Projects; **(4)** structured contributor roles for repeat helpers; **(5)** close stale PRs with a clear reason ("a rejected PR with a clear explanation is still useful"). **[Primary discussion]** — https://github.com/Dokploy/dokploy/discussions/4803
- Growth tactics that are documented: building in public on LinkedIn/X ("After 2 years of building Dokploy in public…"), content-led growth, and a self-hosted product people deploy on their own VPS. **[Primary]** — https://www.linkedin.com/in/carlos-mauricio-ortiz-siu-6b9011184 ; [Secondary profile] https://www.billiondollarpitchdecks.com/startups/dokploy

### 4.3 Paperless-ngx — the community-takeover control case

- When paperless-ng's solo maintainer went silent (~6 months, unanswered), the community organized a takeover *in public issue threads* (#1599, #1632): created a GitHub org, invited existing contributors, defined teams. First release: **contributions from over 50 people, 250+ commits** "since the old repository." Now 40k+ stars, multi-maintainer, still Matrix+Discussions based. **[Primary]** — https://github.com/jonaswinkler/paperless-ng/issues/1599 ; https://github.com/jonaswinkler/paperless-ng/issues/1632 ; https://forum.cloudron.io/topic/6621/paperless-ngx-released-community-driven-version-of-paperless-ng ; https://docs.paperless-ngx.com/
- **Lesson for Orivory:** bus factor is a *design decision*. Paperless-ngx's founders deliberately "distributed the responsibility of advancing and supporting the project among a team of people" — that sentence is in the first paragraph of their docs. Name co-maintainers before you burn out, not after you vanish.

### 4.4 Typebot — Baptiste Arnaud (solo, monetization-first)

- Launched June 2020; stuck at **~$100 MRR for 8 months**; a lifetime deal (SaaS Mantra, April 2021) produced **767 sales / $23,605 / 900+ new users in 3 weeks**; he immediately converted users into a community (Facebook group **330+ members**) plus a **public roadmap** on Trello. By Nov 2024: ~$34K MRR, bootstrapped, still founder-led with "part-time collaborators." **[Primary IH post]** — https://www.indiehackers.com/post/from-1-to-767-paying-users-in-3-weeks-with-no-marketing-effort-c6e1a7eda3 ; [Secondary] https://www.starterstory.com/typebot-breakdown ; [Primary repo] https://github.com/baptisteArno/typebot.io (top contributor: founder 3,674 contributions; #2 human: 72 — **still essentially solo**) ; license note: https://typebot.com/business-continuity
- **Lesson:** a solo project can be commercially healthy without becoming a contributor community; don't assume stars ⇒ contributors. The gap between #1 (3,674) and #2 (72) contributions is the normal solo-project signature.

### 4.5 Karakeep/Hoarder — Mohamed Bassem (side-project discipline)

- Started Jan 2023 as a nights-and-weekends project by a systems engineer ("I didn't want to get too detached from web development… build something I use every day"); grew to **24,800+ stars / 192 contributors** by 2026 — but the founder holds **1,744 contributions vs. #2 at 53**: community of users, thin community of contributors. **[Primary repo]** — https://github.com/mohamedbassem/hoarder-app/ ; [Secondary] https://doolpa.com/article/karakeep
- **Lesson:** users-first growth (AI tagging was the wedge) doesn't automatically produce contributors; converting users requires the explicit machinery of §1.

### 4.6 Twenty, Plausible, Dub, Formbricks (community-engineered growth)

- **Twenty (YC S23):** "more than 300 contributors in the last year and 20,000 stars" at Nov 2024 (TechCrunch) — built deliberately: Discord + public roadmap + Crowdin translations + a plugin/SDK ambition ("hopes there will be an active ecosystem of developers working on extensions and plugins"). By Aug 2026: ~55k stars, **714 contributors, bus factor 5**. **[Secondary + Primary]** — https://techcrunch.com/2024/11/18/twenty-is-building-an-open-source-alternative-to-salesforce/ ; https://repositoryradar.dev/repo/twentyhq/twenty ; https://github.com/twentyhq/twenty
- **Plausible:** growth engine was *content + building in public* (Indie Hackers, then weekly blog posts → 6-7 HN front-page hits) and a one-file self-hosted Docker release "to get buzz in the developer world"; **100+ developers had contributed** and 4,600 stars by Dec 2020; $1M ARR by mid-2022; license switched MIT→AGPL after companies tried to resell without contributing back. **[Primary blog]** — https://plausible.io/blog/building-open-source ; https://plausible.io/blog/open-source-saas ; https://plausible.io/blog/bootstrapping-saas ; https://plausible.io/blog/startup-marketing
- **Dub (Steven Tey):** open-source link shortener that grew to **1,000 paying customers without paid marketing**; "The head of engineering at Twilio first discovered us through our GitHub repo" — the open repo *was* the sales channel; ~18k stars by Oct 2024. **[Primary interview]** — https://www.mintlify.com/blog/founder-mode-dub ; https://ossstartuppodcast.substack.com/p/episode-152-taking-on-bitly-with
- **Formbricks:** ran a gamified contributor program ("FormTribe"): points, levels ("Repository Rookie" → "Formbricks Legend"), a hackathon with 65 prizes (lottery + points); maintainer-reported: "significantly more people wanting to contribute than we have tickets available." Caveats: maintainer-reported numbers, and the README later stated code contributions would be accepted only "as an exception" — gamification produces contribution *volume* that must match real scope. **[Primary posts/talk]** — https://dev.to/jobenjada/making-open-source-contributions-a-game-2m1b ; https://www.coss.community/cossc/ocs-2023-johannes-dancker-formbricks-161c ; https://github.com/formbricks/formbricks

### 4.7 Cross-case synthesis — what year-one interventions correlate with contributor growth

1. **Public responsiveness as a personal routine** (Immich's Reddit streak; Plausible's Twitter searches; Cal.com's community PR team).
2. **Lowering setup friction to near zero** before amplifying demand (Cal.com's contributor docs; Paperless-ngx teams).
3. **A visible scope + roadmap** so community work lands where it merges (Twenty, Dokploy's crisis list, Typebot).
4. **An acquisition wedge beyond GitHub** (Reddit/HN/build-in-public content — Plausible, Immich, Dokploy) — stars follow attention; contributors follow *kept* promises (fast review + merge).
5. **Funding events announced transparently** (Immich/FUTO, Plausible AGPL post) — handled publicly, funding moments built trust rather than spending it.

---

## 5. Trust artifacts for self-hosted OSS: do they measurably move adoption?

- **The one hard number in this space:** GitHub's Open Source Survey (n≈5,500): **93% encountered "incomplete or outdated documentation"** — the most common problem reported in open source — while **60% of contributors rarely/never contribute docs**; **64% say a clear license is very important to using** a project and **67% to contributing** to it. Documentation that explains processes is valued *more* by underrepresented groups. **[Primary survey]** — https://opensourcesurvey.org/2017/ ; data: https://zenodo.org/records/806811 ; press analysis: https://www.infoq.com/news/2017/06/github-survey-open-source/
- **Public metrics:** Cal.com has published an `/open` page since the company's third page existed — weekly active usage, merged PRs, monthly burn, GitHub stars — and treats radical transparency as core strategy. No causal study, but it's a deliberate, sustained trust investment. **[Primary]** — https://cal.com/blog/open-startup
- **Transparency cadence (Immich):** the combination of (a) honest instability warnings, (b) detailed changelogs, (c) public license-change reasoning (https://github.com/immich-app/immich/discussions/7023), and (d) a two-year "we said, here's what happened" retrospective (https://immich.app/blog/futo-two-years-later) is the strongest documented self-hosted trust artifact — again narrative, not A/B-tested. **[Secondary synthesis]** — https://medium.com/@Emily_OnChain/immich-an-open-source-devrel-case-study-57747bb5e5d2
- **Security policy + security.txt:** RFC 9116 (May 2022) standardizes `/.well-known/security.txt` with Contact/Policy/Expires fields; adopted by Google, GitHub, UK MoJ, CISA, and multiple governments. Cost ≈ 1 hour; there is **no published evidence it moves adoption** — its value is enabling responsible disclosure (and it signals operational maturity to exactly the users who self-host sensitive data). **[Primary RFC]** — https://datatracker.ietf.org/doc/html/rfc9116 ; generator/guide: https://securitytxt.org/
- **SLSA / reproducible builds:** SLSA Build L1–L3 (provenance → signed hosted builds → hardened isolated builds). Enterprise adoption is real (npm provenance, PyPI attestations via PEP 740 — https://github.com/ossf/tac/blob/main/process/project-lifecycle-documents/SLSA_graduation_stage.md ), but the cost side is sobering: Tenable Nessus took **~a year of engineering** to reach SLSA L3 (https://ar.tenable.com/blog/strengthening-the-nessus-software-supply-chain-with-slsa). **Honest verdict: no evidence SLSA measurably moves GitHub adoption for small projects.** The cheap 90%-value version for Orivory: GitHub Actions provenance attestations (SLSA L3 via GitHub's hosted builders, one workflow line) + signed container images — do it because it's nearly free, not because it grows stars. FAQ: https://slsa.dev/spec/v1.2/faq
- **Public roadmap + changelog discipline:** directly evidenced as a *community demand* (Dokploy's contributors explicitly asked for "Public Roadmap… GitHub Projects" and a scope doc: https://github.com/Dokploy/dokploy/discussions/4803) and standard practice among the growth cases (Twenty, Typebot, Immich). Treat as table stakes.
- **Bottom line:** the *only* quantified "trust artifact" effects found are documentation-related (93% pain; license importance 64/67%). Everything else (public metrics, security.txt, SLSA, roadmaps) is **low-cost, high-credibility hygiene** with narrative evidence only.

---

## 6. Ecosystem / plugin strategies (how platforms multiply contributors)

- **Obsidian:** grew a community-plugin registry from 0 → milestones of 100/500/1,000/2,000 (tracked at https://www.moritzjung.dev/obsidian-stats/pluginstats/milestones/) to **7,095 plugins listed** (snapshot 2026-03: https://www.obsidianstats.com/plugins; another tracker counts 2,698 actively tracked: https://plugin.observer/ecosystem). The enabling infrastructure: a stable plugin API, a **template/sample plugin repo** to scaffold from, a human **review process** for the community list, and an **in-app directory**. **[Primary/trackers]** — also official sample plugin pattern documented in Obsidian dev docs.
- **Home Assistant:** **2,000+ built-in integrations** ship in core (https://www.influxdata.com/blog/9-home-assistant-integrations-how-use-them/ ; official architecture: integrations are Python components under `homeassistant.components`: https://developers.home-assistant.io/docs/architecture_components/), plus a separate **custom-components channel (HACS)** with a third-party install-count analytics project (https://github.com/Vaskivskyi/ha-custom-analytics). HA's integration *quality scale* + docs requirements are the review scaffold that lets thousands of integrations exist.
- **Grafana:** plugin ecosystem = **SDK + developer portal + open-source example plugins + an in-app catalog** (browse/install/update/deprecation status) with community plugins distributed in the same catalog and supported via the community forum/Slack. **[Primary]** — https://grafana.com/grafana/plugins/ ; https://grafana.com/blog/data-sources-visualizations-and-apps-a-guide-to-extending-and-customizing-grafana/
- **Figma:** marketplace-scale proof that a plugin economy multiplies reach — one indie developer reports **2,000,700+ plugin installs** across their catalog. **[Secondary]** — https://www.hypermatic.com/figma-plugin-workflow-data/
- **Twenty** is the in-flight example of a CRM deliberately building toward "an active ecosystem of developers working on extensions and plugins" with an SDK release train (`sdk/v2.30.0`). **[Secondary]** — https://techcrunch.com/2024/11/18/twenty-is-building-an-open-source-alternative-to-salesforce/ ; https://repositoryradar.dev/repo/twentyhq/twenty
- **Minimal viable ecosystem infrastructure** (distilled from what all four actually built):
  1. A **manifest + loader** (you already have the hard part: an API surface).
  2. A **template repo** ("create-your-first-connector" scaffold — Obsidian's sample plugin, Grafana's examples).
  3. **Docs page** for plugin authors (one page is enough to start).
  4. A **directory** (even a static gallery page or GitHub topic) — discovery is what makes the ecosystem a market rather than a graveyard.
  5. A **light review/publish process** (Obsidian's review, Grafana's catalog submission) — but defer this until there are ≥5 third-party things to review.
- **Gap:** I found no published numbers on the *timing* (e.g., "ecosystem program launched month N → contributor growth +X%"). The multiplier claim rests on the registry sizes above plus Obsidian/Grafana/HA's deliberate infra investments.

---

## 7. Foundation / fiscal sponsorship: when does it matter?

- **CNCF Sandbox (the standard "first rung") requires — before you can even apply cleanly:** Apache-2.0 or a CNCF-allowlist license (BSL/GPL family **not** acceptable); a **MAINTAINERS.md** with a Name/GitHub-ID/Organization table; **minimum 3 maintainers from 2+ different organizations** (employers, not GitHub orgs); separation from any parent project's org; **5–7 adopters willing to be interviewed**; TOC sponsor + vote; signed Contribution Agreement + **trademark transfer to the Linux Foundation**; the process runs **5–15 months**. **[Primary]** — https://contribute.cncf.io/projects/lifecycle/ ; https://github.com/cncf/toc/blob/main/process/README.md ; https://github.com/cncf/sandbox/blob/main/README.md
  - **Verdict for Orivory:** categorically not applicable yet — a solo MIT founder fails the 3-maintainers/2-orgs bar by definition. Foundation membership is a *scaling outcome*, not a growth tactic. (Alternatives named by CNCF for non-cloud-native projects: e.g., CommonHaus, SPI, language foundations — https://github.com/cncf/sandbox/blob/main/README.md.)
- **Open Collective / Open Source Collective (fiscal hosting):** OSC hosts **3,500+ open-source projects**, accepts "most open source projects, in any language, anywhere in the world," and charges a flat **10% of incoming funds** for legal/financial/admin services (contracts signed on your behalf, no Stripe/business entity needed). **[Primary]** — https://oscollective.org/projects/
- **GitHub Sponsors:** GitHub charges **no platform fee** ("GitHub does not charge a fee" — via the fiscal-host flow documented by OSC: https://docs.oscollective.org/campaigns-and-partnerships/github-sponsors). For an individual, Sponsors + a `FUNDING.yml` is the zero-cost default; community-maintained comparisons put realistic solo-maintainer sponsor income at ~**$1k–$5k/month** and note Polar as the B2B-friendlier MoR alternative (~4% + processing, handles VAT/invoices). **[Secondary comparison]** — https://www.youngju.dev/blog/culture/2026-05-14-oss-funding-2026-github-sponsors-open-collective-polar-tidelift-ko-fi-developer-sponsorship-deep-dive.en ; HN debate on fees/positioning: https://news.ycombinator.com/item?id=36722702
- **Small-project example:** Dokploy (30k+ stars) still runs a modest Open Collective page listing 144 contributors and a handful of financial backers — i.e., even at 30k stars, *community fiscal infrastructure generates small money*; it is credibility + bookkeeping, not income. **[Primary]** — https://opencollective.com/dokploy
- **Single-patron alternative:** Immich's FUTO deal shows the non-foundation path: one nonprofit funder, full-time team, autonomy retained, all announced with a public Q&A and revisited two years later (§4.1). **[Primary]** — https://immich.app/blog/futo-two-years-later
- **Decision rule:** (a) day one — GitHub Sponsors + FUNDING.yml (zero fees, zero entity); (b) first recurring cost or first corporate invoice — Open Collective/OSC (10% buys you a legal entity and books); (c) foundation — only when you have ≥3 maintainers across ≥2 employers and a brand worth protecting (trademarks are what foundations actually hold).

---

## 8. Docs & demo: docs as first impression, hosted demo with fake data

- **Docs are the #1 documented pain in OSS (93%** hit incomplete/confusing documentation; license clarity is the #2 — 64% usage / 67% contribution importance): https://opensourcesurvey.org/2017/ — so the "docs as first impression" argument has direct survey evidence behind it.
- **Docs reduce maintainer load (first-hand):** Documenso's early team wrote that before good contributor docs "we received the same questions… over and over again. The documentation significantly reduced the number of repetitive questions… fewer repetitive questions to handle." **[Primary first-person]** — https://catalins.tech/how-i-got-my-dev-job-on-twitter/
- **Hosted demo instances (verified examples):** Cal.com runs a dedicated demos page with seeded booking demos and embed patterns — https://demo.cal.com/ ; Paperless-ngx announced a demo instance alongside its first release ("there's a demo now too") — https://forum.cloudron.io/topic/6621/paperless-ngx-released-community-driven-version-of-paperless-ng ; Documenso lists an official demo (https://selfhost.directory/project/documenso). PostHog also markets a live product demo, though I did not verify its current URL in this session (**gap: PostHog demo URL unverified here**).
- **Docs-stack trends (2025–2026):** Nextra remains the default Next.js docs theme (powers Vercel/tRPC/SWR docs); **Fumadocs** is the fastest-growing Next.js-native alternative (~**10,300 GitHub stars as of Jan 2026**, headless, OpenAPI-first-class); Docusaurus still wins for versioning/i18n at scale; Mintlify is the polished hosted SaaS (~**$150/mo** startup tier); Starlight (Astro) wins static-first i18n. For a Next.js product like Orivory, Fumadocs or Nextra keeps docs in-repo, free, and self-hosted — matching the values of a self-hosted-OSS audience (docs sites that themselves are closed SaaS read oddly to this crowd). **[Secondary comparisons]** — https://www.pkgpulse.com/guides/fumadocs-vs-nextra-v4-vs-starlight-documentation-sites-2026 ; https://docsio.co/blog/fumadocs ; https://trybuildpilot.com/432-mintlify-vs-nextra-vs-starlight-docs-2026 ; https://www.stackfyi.com/guides/docs-platforms-mintlify-vs-docusaurus-vs-nextra-vs-fern-2026
- **Translations:** the growth cases route i18n through Crowdin (Twenty: https://github.com/twentyhq/twenty ; Paperless-ngx: https://crowdin.com/project/paperless-ngx) — cheap contributor on-ramp for non-coders, aligned with all-contributors recognition (§1.5).

---

## 9. Recommended playbook for a solo-maintainer MIT project (ranked by impact ÷ effort)

Scale: **Impact** = expected effect on contributors/users for Orivory specifically (evidence-weighted); **Effort** = solo-maintainer hours to stand up + ongoing. Ratio is qualitative but grounded in the sections above.

| # | Action | Impact | Effort | Why (evidence) |
|---|--------|--------|--------|-----------------|
| 1 | **One-command contributor env**: `docker compose` dev stack w/ seeded fake data + `.devcontainer/devcontainer.json` + "Open in GitHub Codespaces" badge | ★★★★★ | ~1 day setup, ~0 ongoing | Workspace setup is the worst-covered CONTRIBUTING barrier (28% coverage, §1.2); devcontainer case reports PRs from people who couldn't build locally otherwise (§1.4); directly enables your two-process FastAPI+Next.js app |
| 2 | **CONTRIBUTING.md that covers the 6 newcomer barriers** (esp. "pick a task" + "get running" + "how to reach a human"), linked prominently from README | ★★★★★ | 0.5–1 day, update as scope changes | First-pull acceptance 51%→64%→95% with insertion+updates (§1.2); "decisive signal" in contributor interviews (§1.2) |
| 3 | **Maintained `good first issue` label + strict small-task hygiene** (≤1 file-ish tasks, docs/typos/translators allowed) | ★★★★☆ | ~1–2 h/week triage | GFI → **5.57× acceptance odds** (§1.3); fast expert response (median 8.5 h) is what makes GFIs work (§1.3) |
| 4 | **Response SLA you can keep**: ack every issue/PR ≤7 days (even "seen, not scheduled") | ★★★★☆ | ~2 h/week | Dokploy's 10/100 feedback-loop crisis is the negative proof; social barriers (no answer) are the #1 documented newcomer blocker (§1.1, §4.2) |
| 5 | **Hosted demo with fake data** + link in README ("try before you clone") | ★★★★☆ | 0.5–1 day + small hosting cost | Verified pattern: demo.cal.com, Paperless-ngx demo, Documenso demo (§8); for a second-brain product, a demo *is* the pitch |
| 6 | **Public roadmap on GitHub Projects + monthly changelog/release-notes cadence** | ★★★★☆ | 1–2 h/month | Explicit community demand at Dokploy (§4.2); standard across Twenty/Typebot/Immich; pairs with honest status warnings (Immich) |
| 7 | **Docs site** (Fumadocs or Nextra, in-repo, free) with: quickstart, self-host guide, architecture page, plugin/connector author page | ★★★★☆ | 2–4 days | 93% docs pain (§5, §8); Documenso's repetitive-question reduction (§8); in-repo docs fit self-hosted values |
| 8 | **GitHub Discussions (support archive) + one chat (Discord)**; decisions and answers of record stay on GitHub | ★★★☆☆ | ~1 h/week | HA's 163k-member Discord shows chat-only loses knowledge (§3.1); Paperless-ngx/Jellyfin chose indexable channels deliberately |
| 9 | **all-contributors table + Crowdin translations** | ★★★☆☆ | ~0.5 day | 2,000+ projects use the spec (§1.5); translations are the best non-code contributor funnel (Twenty/ngx, §8) |
| 10 | **GitHub Sponsors + FUNDING.yml + security policy + `security.txt` on the demo/docs domain** | ★★☆☆☆ (adoption) / ★★★☆☆ (credibility) | ~0.5 day total | Zero-fee default funding (§7); RFC 9116 (§5); no adoption effect measured — pure hygiene |
| 11 | **Targeted small bounties** (docs/examples/connectors, $50–$200) — *only after* #1–#4 exist and only with review capacity | ★★☆☆☆ | variable, review-heavy | Algora works as acquisition but review time is the constraint; AI-slop attempts are the documented failure mode (§2) |
| 12 | **Deliberately name a 2nd/3rd committer** within the first year (triage/docs roles) | ★★★★☆ (long-run) | ongoing | Paperless-ngx exists *because* of bus factor; Jellyfin's constitution is the mature form (§3.1, §4.3); CNCF's 2-org bar shows where this eventually matters |
| — | **Skip for now:** RFC/PEP-style process (negative-EV at solo scale, §1.6); Hacktoberfest (spam externality, §3.3 — if ever, opt-in with triage budget); foundation membership (requirements unmet, §7); full plugin marketplace (build template + directory first, §6) | | | |

### First 90 days (concrete)

**Week 1 — Foundations (effort ≈ 2–3 days)**
- [ ] `docker compose` dev environment with seeded demo data + README quickstart ("clone → running in ≤10 min").
- [ ] `.devcontainer/devcontainer.json` + "Open in GitHub Codespaces" badge.
- [ ] CONTRIBUTING.md covering: how to pick a task (label meanings), how to run tests, PR expectations, and how to get a human answer (link chat + Discussions).
- [ ] GitHub Sponsors + `FUNDING.yml`; `.github/SECURITY.md` (private-vuln reporting) + `/.well-known/security.txt` on the docs/demo domain.
- [ ] Issue templates (bug/feature) + PR template; enable Discussions with a "support" category that redirects to discussions, not issues.

**Weeks 2–4 — Seed the funnel (≈ 2 days + upkeep)**
- [ ] Label 8–12 real `good first issue`s (docs, small fixes, a connector each) — keep them truly small; add `help wanted` for bigger ones.
- [ ] Ship the docs site (Fumadocs/Nextra): Quickstart, Self-hosting, Architecture, "Build your first connector" page.
- [ ] Stand up the hosted demo instance (fake personas/notes/memories) and link it from README + docs.
- [ ] Create the GitHub Projects roadmap (Now / Next / Later) and write the scope paragraph ("what Orivory is and isn't" — Dokploy lesson).
- [ ] Set the SLA: ack every new issue/PR within 7 days; calendar block 2×/week for triage; install a greeting bot *for triage sorting only*.

**Month 2 — Community surface (≈ 2 days)**
- [ ] Open Discord (one #support, one #contributors channel) and cross-link to Discussions; pin the rule: answers of record get mirrored to Discussions/GitHub.
- [ ] Add all-contributors bot; first recognition PR (docs/translators count).
- [ ] Enable Crowdin for UI strings; add translation as a documented contribution type.
- [ ] Publish changelog #1 (monthly cadence from here): what shipped, what broke, what's next (Immich-style honesty about breaking changes).

**Month 3 — First proof points (≈ 1–2 days)**
- [ ] Ask 3 early users to become triage/docs co-maintainers with explicit write scope (docs, issue labels); add them to README + a TEAM.md.
- [ ] Publish one "build a connector with me" walkthrough (post/video) using the template repo; list every connector in a public directory (docs page or topic tag).
- [ ] Metrics to watch (from the evidence above): **time-to-first-response**, **time-to-first-PR**, **% of GFIs merged within 30 days**, repeat-contributor count (the Qiu/Gaughan/ICSE metrics that actually predict community formation).
- [ ] Review whether a $50–$200 bounty (via Algora/Polar) on 2–3 connector docs/examples makes sense *this* quarter — only if review bandwidth exists.

---

## Key takeaways

1. **Responsiveness is the highest-verified growth mechanic** — social/no-answer barriers appear in 75% of newcomer studies, and GFI-mentoring data shows median first expert reply in 8.5 h. A kept 7-day ack SLA beats every bot and badge. (https://dl.acm.org/doi/10.1016/j.infsof.2014.11.001 ; https://dl.acm.org/doi/10.1109/ICSE48619.2023.00064)
2. **`good first issue` labels have the strongest single measured effect: 5.57× odds of a newcomer's first patch being accepted** — but only if such issues actually stay small and get fast reviews. (https://doi.org/10.48550/arxiv.2407.04159)
3. **CONTRIBUTING.md works when maintained and when it covers task-picking + workspace setup** (acceptance lift 51%→95% in the temporal study; ~65% of projects lack one; 75%+ never explain how to choose a task). It is not magic: large-sample work finds no *causal* growth effect — it removes friction for people already arriving. (https://doi.org/10.5753/semish.2025.6870 ; https://par.nsf.gov/servlets/purl/10493930 ; https://arxiv.org/pdf/2502.18440)
4. **Zero-setup contributor environments (devcontainer + compose + seeded data + Codespaces badge) attack the worst-covered barrier and cost ~a day.** Measure time-to-first-PR. (https://medium.com/@askpt/dev-containers-removing-friction-to-accelerate-contributor-onboarding-391c09ccfbb2)
5. **Bounties buy attempts, not contributors.** Algora's documented scale ($65,785 / 600 bounties / 188 contributors at launch) and 2026 saturation (8–158 attempts within hours; a $341 bounty with 236 claims open for 21 months) show review time, not money, is the bottleneck; even Polar says "we don't believe in traditional bounties." Use small, scoped bounties only with review capacity. (https://medium.com/@giannis_34055/algora-open-source-coding-bounties-5083edc5327f ; https://dev.to/aion_autonomous_org/i-measured-the-open-source-bounty-market-before-entering-it-then-i-didnt-enter-93n ; https://rishi.app/blog/polar)
6. **Discord is where self-hosters are, but chat loses knowledge** — Home Assistant (163k-member Discord) fights lost-support-thread entropy with role-gating, while Paperless-ngx/Jellyfin deliberately keep support on GitHub Discussions/Matrix for indexability. Chat for responsiveness + Discussions for the record. (https://community.home-assistant.io/t/discord-changes-are-now-live/771238 ; https://docs.paperless-ngx.com/)
7. **Dokploy (30k stars/270 contributors in <2 years, solo) is the cautionary tale:** ~500 open issues + 180+ silent PRs scored its contributor feedback 10/100. The community's fix list — 7-day acks, public scope, GitHub-Projects roadmap, contributor roles — is a free playbook. (https://github.com/Dokploy/dokploy/discussions/4803)
8. **Immich's flywheel was transparency, not features:** prototype video on r/selfhosted, +30k stars and 900+ contributors in 2024, honest "don't trust it with your only photos" warning, public license-change reasoning, FUTO funding announced and re-audited in public. (https://immich.app/blog/2024-year-in-review ; https://immich.app/blog/futo-two-years-later)
9. **Stars ≠ contributors:** Typebot (~$34K MRR) and Karakeep (24.8k stars) remain >96% solo by contribution share; Twenty is the counter-case that engineered community (300+ contributors/yr) with Discord + roadmap + Crowdin + SDK. Decide which you're building. (https://github.com/baptisteArno/typebot.io ; https://github.com/mohamedbassem/hoarder-app/ ; https://techcrunch.com/2024/11/18/twenty-is-building-an-open-source-alternative-to-salesforce/)
10. **Trust artifacts are cheap hygiene, not growth levers — with one exception:** the only quantified trust numbers are documentation (93% pain) and license clarity (64/67% importance). security.txt (RFC 9116) and SLSA provenance cost ~nothing (GitHub-native attestations) but have no measured adoption effect; public metrics (cal.com/open) and changelogs are sustained narrative investments. (https://opensourcesurvey.org/2017/ ; https://datatracker.ietf.org/doc/html/rfc9116 ; https://cal.com/blog/open-startup)
11. **Ecosystems multiply contributors through five pieces of infra:** API+manifest, template repo, author docs, a public directory, and (later) a review process — Obsidian's registry scaled to ~7,095 plugins on exactly this; defer the marketplace until ≥5 third-party things exist. (https://www.obsidianstats.com/plugins ; https://grafana.com/grafana/plugins/)
12. **Foundations are for later:** CNCF Sandbox demands 3 maintainers from 2+ organizations and takes 5–15 months; the solo path is GitHub Sponsors (0% fee) → Open Collective/OSC (10%, 3,500+ projects hosted) when money or contracts get real — and naming co-maintainers before burnout is the Paperless-ngx lesson. (https://contribute.cncf.io/projects/lifecycle/ ; https://oscollective.org/projects/ ; https://docs.oscollective.org/campaigns-and-partnerships/github-sponsors ; https://docs.paperless-ngx.com/)

---

## Appendix: source-quality caveats

- Discord member counts are third-party tracker snapshots (disdex.io) or platform listings; treat as ±.
- The 2026 Algora saturation figures come from practitioner blog experiments, not platform reporting; direction (review-time scarcity, AI-generated attempt flood) is corroborated by the peer-reviewed huntr-maintainers study (https://arxiv.org/html/2409.07670v1).
- Maintainer-reported program results (FormTribe gamification, Dokploy milestone post, Polar's bounty experiment) are first-party claims; treat as experience reports, not measurements.
- Documented evidence gaps (searched, not found): (a) any study of welcome-bot/stale-bot effects on contributor counts; (b) before/after contributor numbers attributable to office-hours/community calls; (c) PostHog demo URL verification; (d) a clean bounty→contributor-count causal series for any single repo; (e) current Algora platform-wide payout totals (only the 2023 verified figure used).
