# Orivory — User Research: Who wants a self-hosted AI second brain, what hurts, and what they'll pay for

**Date:** 2026-09-02
**Author:** Desk research (delegated subagent), via Exa web search + page fetch. ~25 distinct searches/fetches across Reddit-adjacent sources, Hacker News threads, GitHub issues, official pricing pages, and product reviews.

---

## Method & limitations

- **Desk research only — no primary interviews.** All findings are from public discussions (Hacker News, Reddit/Lemmy mirrors, GitHub issues), vendor pricing pages, and third-party product reviews. Quote sentiment, not market size precision.
- **Community sizes are approximate** and drawn from third-party trackers (GummySearch, Hive Index, ReddTrends) which disagree with each other by ±10%; ranges are given where sources conflict.
- **Search-index dates are noisy**: some sources carry 2026 dates that may reflect index metadata rather than publication dates; where a claim is time-sensitive (pricing), the pricing page itself was checked.
- **Selection bias**: people who post on HN/Reddit/GitHub over-index on technical, privacy-conscious, self-hosting users — the segment Orivory targets. Complaints from non-technical mass-market users (Notion consumers) are included for contrast but are not Orivory's core audience.
- Every factual claim below carries an inline source link. Claims without a URL were not included.

---

## 1. SEGMENTS — who actually uses / wants self-hosted AI second brains

### Community size evidence (demand-side market)

| Community | Size | Growth | Source |
|---|---|---|---|
| r/selfhosted | ~821–830K members | +245K/yr (+42%/yr) | [Hive Index](https://thehiveindex.com/communities/r-selfhosted/), [GummySearch](https://gummysearch.com/r/selfhosted/) |
| r/LocalLLaMA | ~815K members | +286K/yr (+54%/yr) | [GummySearch](https://gummysearch.com/r/LocalLLaMA/), [ReddTrends](https://www.reddtrends.com/r/localllama) |
| r/ObsidianMD | ~359K members | +115K/yr (+47%/yr) | [GummySearch](https://gummysearch.com/r/ObsidianMD/), [ReddTrends](https://www.reddtrends.com/r/obsidianmd) |
| r/notebooklm | ~148K members | +96K/yr (+183%/yr) | [GummySearch](https://gummysearch.com/r/notebooklm/) |
| r/NoteTaking | ~65K members | +30K/yr (+88%/yr) | [GummySearch](https://gummysearch.com/r/NoteTaking/) |

### Competitor traction (supply-side validation)

| Project | GitHub stars | Notes / source |
|---|---|---|
| AnythingLLM | ~65K | Positioned "no frustrating setup required"; multi-user workspaces ([repo](https://github.com/mintplex-labs/anything-llm)) |
| Khoj | ~36.7K | YC S23; WhatsApp/Obsidian/Emacs clients; open-source, self-hostable ([repo](https://github.com/khoj-ai/khoj/)) |
| Karakeep (ex-Hoarder) | ~28.7K | Bookmark-everything + AI tagging; 701 open issues at time of snapshot ([repo](https://github.com/karakeep-app/karakeep)) |
| Reor | ~8.6K | **Repo now ARCHIVED** — local-first AI notes could not sustain development ([repo](https://github.com/reorproject/reor)) |
| OpenKnowledge (HN Show) | 381 points / 173 comments | "Open source AI-first alternative to Obsidian/Notion" with built-in MCPs ([HN thread](https://news.ycombinator.com/item?id=48675435)) |
| Rowboat (HN Show) | 205 points / 56 comments | Local-first "work memory" knowledge graph for agents ([HN thread](https://news.ycombinator.com/item?id=46962641)) |

**HN engagement confirms the category is hot and contested**: multiple Show HNs in recent months target exactly Orivory's positioning — self-hosted, semantic, agentic personal knowledge bases ([Atomic](https://news.ycombinator.com/item?id=47470433), [Kai](https://news.ycombinator.com/item?id=45045793), [Memento](https://news.ycombinator.com/item?id=48557937), [Karpathy-style LLM wiki](https://news.ycombinator.com/item?id=47899844)).

### The 5 distinct segments

1. **Self-hosters / homelabbers (~830K-strong community).** Already run Docker, want notes under their own roof; hate sync dependence and vendor lock-in. Active demand thread: "Self hosted web based note application" — dozens of tool suggestions; top complaint "tired of waiting for sync before accessing my notes on different devices" ([Lemmy/feddit mirror of r/selfhosted thread](https://gammel.feddit.dk/post/55835), [piefed Notion-replacement thread](https://piefed.social/c/selfhosted/p/1875507/what-s-the-best-open-source-selfhostable-notion-replacement)).
2. **Privacy-conscious knowledge workers (PKM mainstream).** 359K on r/ObsidianMD; choose tools explicitly on a privacy-vs-capability axis — Smart Connections (local, no cloud) vs Copilot (sends vault to OpenAI) ([codeculture comparison](https://codeculture.store/blogs/developer-culture/obsidian-ai-plugin-comparison-2025)). Notion's cloud trust problem is a recurring migration driver ([ejl.st](https://ejl.st/notion-kinda-sucks/)).
3. **Developers / AI builders.** Want their second brain readable/writable by agents via MCP; HN commenters on Atomic: "MCP server approach makes total sense… I would love to wire a stop hook to automatically atomize session insights — that's the dream" ([HN](https://news.ycombinator.com/item?id=47470433)); Karpathy's LLM-wiki pattern spread across dev communities ([HN wiki thread](https://news.ycombinator.com/item?id=47899844)).
4. **Students / researchers / heavy content consumers.** NotebookLM's community exploded +183%/yr to ~148K; Recall markets to "500K professionals, students and lifelong learners" ([App Store](https://apps.apple.com/us/app/recall-summarize-save/id6445893722)) and offers student discounts ([Nubia review](https://nubiapage.com/recall-ai/)).
5. **Small teams / workspaces.** Want shared knowledge with access control but on their own infra: AnythingLLM's "multi-user workspaces designed for teams" ([aifoss Khoj review](https://aifoss.dev/blog/khoj-review-2026/)); a family self-hoster wants "a joint space for notes" for family members ([piefed thread](https://piefed.social/c/selfhosted/p/1875507/what-s-the-best-open-source-selfhostable-notion-replacement)). Enterprise-grade self-hosted RAG (Onyx) shows the top of this market ([docs](https://docs.onyx.app/admins/connectors/official/github)).

---

## 2. PAINS — what people complain about with current solutions

### Retrieval quality / hallucinations (the most damning, recurring theme)

- Obsidian Copilot: "[Relevant Notes] Copilot retrieves irrelevant notes" — wrong results across models, inflated similarity scores, persisted across versions ([issue #1224](https://github.com/logancyang/obsidian-copilot/issues/1224)).
- Smart Connections: "[Bug]: irrelevant connections… all scored 1.0" ([issue #1287](https://github.com/brianpetro/obsidian-smart-connections/issues/1287)); chat "cannot find all and every information in all of my notes… I am much better off using a simple search function" ([issue #305](https://github.com/brianpetro/obsidian-smart-connections/issues/305)).
- Local-model RAG is often just bad: Reor HN feedback — "'related notes' feature didn't provide much value… so weak it was nonsensical. The Q&A mode… asking anything specific typically just resulted in less than helpful or false answers" ([HN](https://news.ycombinator.com/item?id=39372159)). The MindForger developer gave up on local RAG entirely: "the performance was poor… and the actual responses were rarely useful (off-topic and impractical responses, hallucinations)" ([same thread](https://news.ycombinator.com/item?id=39372159)).
- Notion AI: "incapable of finding even basic things that I knew were in my notes… it seems to hallucinate more than I'm used to" ([ejl.st](https://ejl.st/notion-kinda-sucks/)).
- NotebookLM: forced model migration "completely broke RAG & grounding — the AI actively gaslights me, claiming the documents don't exist… when the retrieval step fails, it refuses to just say 'I don't know'" ([Google AI Developers Forum](https://discuss.ai.google.dev/t/critical-regression-gemini-3-1-pro-update-feb-19-completely-broke-notebooklm-s-rag-grounding/126857)); accuracy "drops as you approach the source limit" ([XDA](https://www.xda-developers.com/notebooklms-source-limit-is-its-biggest-problem/)).
- A synthesized answer "reads smoothly whether or not it pulled the right sources, so you learn to click through to the citations every time — which quietly erodes the time savings" (Mem, 1-year review, [dev.to](https://dev.to/pickuma/mem-review-ai-organized-notes-one-year-on-4h83)).

### Setup friction / docker networking hell

- AnythingLLM×Ollama: "Cannot connect to Ollama in Docker Compose setup — UI shows '--loading available models--' forever"; maintainer points to a troubleshooting doc that "exists explicitly for people who run into this" ([issue #3656](https://github.com/Mintplex-Labs/anything-llm/issues/3656)).
- Open WebUI: "90% of 'Open WebUI can't see my models' problems come down to a single networking mistake" ([WikiWayne guide](https://wikiwayne.com/blog/open-webui-ollama-connection-guide)).
- Self-hosted RAG stack generally: "the setup takes an hour, maybe two if you hit Docker networking issues" ([Silverthread Labs](https://www.silverthreadlabs.com/blog/local-ai-setup-guide)).
- Onyx/Danswer: connectors stuck "Initial Indexing"/"Deleting" for days, root causes as exotic as a `/etc/localtime` bind mount breaking Celery UTC assumptions ([#8379](https://github.com/onyx-dot-app/onyx/issues/8379), [#11379](https://github.com/onyx-dot-app/onyx/issues/11379), [#1378](https://github.com/danswer-ai/danswer/issues/1378)).

### Connector quality & ingestion gaps

- Onyx connector failures across File/Web/Confluence/BookStack are a recurring issue class ([#2569](https://github.com/danswer-ai/danswer/issues/2569), [#3227](https://github.com/onyx-dot-app/onyx/issues/3227)).
- Karakeep: server-side crawler can't capture paywalled/authenticated content; Safari client-side capture "Only the article preview/teaser is saved" ([issue #2814](https://github.com/karakeep-app/karakeep/issues/2814)).
- Khoj: "The cloud gap is real… WhatsApp integration, certain automation triggers, and the computer-control agent are more polished on the cloud. There's no version that gives you both [privacy and convenience] fully" ([aifoss review](https://aifoss.dev/blog/khoj-review-2026/)).

### Memory/organization quality — "the AI can't tell me where my notes are"

- NotebookLM: "no global search across notebooks… I've started abandoning notebooks instead of revisiting them" ([XDA](https://www.xda-developers.com/notebooklm-limitations/)).
- Mem: "when the AI is confidently wrong about what you meant, you can't always tell"; "the more your notes lean toward long-lived reference documents… the less the AI-organized model pays off" ([dev.to review](https://dev.to/pickuma/mem-review-ai-organized-notes-one-year-on-4h83)).
- Embedding quality ceiling: local quantized models (384-dim MiniLM) "will miss nuanced conceptual relationships" vs cloud embeddings ([Starlog on Smart Connections](https://starlog.is/articles/ai-dev-tools/brianpetro-obsidian-smart-connections)).

### Performance at scale

- Smart Connections: "Around 8,000-10,000 notes, users report noticeable lag (500ms-1s)… For researchers with 20,000+ files, Smart Connections becomes sluggish enough to disrupt flow state"; a user with 5,768 files: indexing "would take all night… I give up" ([Starlog](https://starlog.is/articles/ai-dev-tools/brianpetro-obsidian-smart-connections); [issue #1244](https://github.com/brianpetro/obsidian-smart-connections/issues/1244)).
- Notion: "with all your data on Notion's servers… a database of 10,000 notes? Forget it. It just plain doesn't scale well" ([ejl.st](https://ejl.st/notion-kinda-sucks/)).

### Cost of LLM APIs / local hardware

- Local inference all-in cost: RTX 4090 ≈ $104/month amortized (hardware + electricity + maintenance time); below ~8M tokens/month vs GPT-4o, cloud is cheaper ([break-even calculator](https://www.kunalganglani.com/blog/local-llm-cost-breakeven)); realistic setups need $1,500–4,000 upfront + 5–10 h/month maintenance ([aisuperior](https://aisuperior.com/cost-of-running-local-llm/)).
- r/LocalLLaMA culture: "Freedom arrives with maintenance costs that many users did not anticipate… local LLM tools remain enthusiast-oriented rather than consumer-ready" ([remio analysis of Reddit sentiment](https://www.remio.ai/post/localllama-on-reddit-open-models-win-freedom-lose-simplicity)).
- Plugin-level API costs confuse users: "I put $5 into openai credits, before that it would not work at all. This was not covered in the documentation" ([Smart Connections #997](https://github.com/brianpetro/obsidian-smart-connections/issues/997)).

### Maintenance burden of self-hosting

- Khoj: "Budget 1–2 hours per month for updates. If that's too much overhead…" ([aifoss](https://aifoss.dev/blog/khoj-review-2026/)).
- Self-hosted RAG: "plan half a day a month for model swaps and re-benchmarking. This is real work, and it is the price of not paying a vendor"; plus "power and heat: two 3090s under load pull ~700 W" ([DEV self-hosted RAG guide](https://dev.to/mryadavgulshan/self-hosted-rag-a-production-pipeline-on-your-own-hardware-2a5i)).

### Trust / privacy anxiety about agentic access

- "What's holding me back from AI repos and agents… is the lack of granular control… the idea of large amounts of personal data being accessible, unchecked, to an AI is concerning" (Atomic HN commenter, [thread](https://news.ycombinator.com/item?id=47470433)).
- AnythingLLM shipped a critical RCE (CVSS 9.6) in March 2026 — self-hosted ≠ automatically safe ([DEV roundup](https://dev.to/thegatewayguy/the-local-llm-stack-in-2026-what-actually-works-ib1)).
- Notion account-termination fear: "if they feel you have violated their TOS… you lose access to all your notes. I've heard of this happening repeatedly" ([ejl.st](https://ejl.st/notion-kinda-sucks/)).

### Sync conflicts / offline

- "I love both [Joplin and Obsidian] but am tired of waiting for sync before accessing my notes on different devices" ([Lemmy selfhosted thread](https://gammel.feddit.dk/post/55835)).
- Karakeep mobile has no offline cache: "Knowing that I can't access [my bookmarks] without a server connection is a dealbreaker" — 51 👍, open >1 year ([issue #1077](https://github.com/karakeep-app/karakeep/issues/1077)).

---

## 3. WHY PEOPLE LEAVE / DON'T ADOPT

- **Capture friction is the #1 killer.** "Capturing a thought takes twenty seconds. This is the killer… The moment writing something down feels like work, you stop doing it. You go back to texting yourself. The workspace dies quietly" (Notion quitter, [Medium](https://medium.com/@lekhanshojha/notion-for-personal-use-why-i-quit-after-a-year-and-what-i-use-instead-5db6106fab82)). Another: "By the third week, my ideas were landing in a text file on my desktop… Notion's inbox had maybe twelve entries across the entire six weeks" ([Kay Foxley](https://oh-kayyyy.medium.com/everyone-recommends-notion-ive-abandoned-it-three-times-ef2fcad2ef22)). Even NotebookLM's mobile capture is called out: "You have to navigate a web interface, which is far too slow for capturing thoughts in real time" ([Android Police](https://www.androidpolice.com/stop-using-notebooklm-as-direct-replacement-to-onenote-evernote/)).
- **Tinkering/maintenance spiral beats actual usage.** "I had a using habit. I had a building habit" — ~20 hours building a system used "maybe twice a week" ([Kay Foxley](https://oh-kayyyy.medium.com/everyone-recommends-notion-ive-abandoned-it-three-times-ef2fcad2ef22)); "You don't 'finish' setting up Notion… Week one is fun. Week six is where workspaces go to die" ([Medium](https://medium.com/@lekhanshojha/notion-for-personal-use-why-i-quit-after-a-year-and-what-i-use-instead-5db6106fab82)); "spends a great deal of time just designing and maintaining their PKM, which takes away from time that you should be spending on writing notes" ([ejl.st](https://ejl.st/notion-kinda-sucks/)).
- **Tools become dumping grounds; value is never retrieved.** "They all become a dumping ground… a landfill of half baked stale todos, notes, pages, links, tags" ([nuric blog](https://www.doc.ic.ac.uk/~nuric/posts/misc/stopped-using-notion-for-more-productivity/)); HN: "Notes apps are where ideas go to die" ([thread](https://news.ycombinator.com/item?id=36136179)); Ask HN: "My own 'second brain' became a graveyard of good intentions: the organizing tax was higher than the value I got back" ([HN #46826277](https://news.ycombinator.com/item?id=46826277)).
- **"I deleted my second brain."** The essay + HN discussion: "In trying to remember everything, I outsourced the act of reflection… The more my system grew, the more I deferred the work of thought to some future self… That self never arrived." Counterpoint from commenters: functional logs (howtos, maintenance logs) survive; aspirational hoarding dies ([HN #44402470](https://news.ycombinator.com/item?id=44402470)).
- **Churn is structural in this category.** Note-app maker (Supernotes) on HN: "we have seen that users who say they have come to our app after trying many other note-taking apps are much more likely to churn, regardless of if we have the features they say they are looking for" ([HN #36136179](https://news.ycombinator.com/item?id=36136179)).
- **Vendor kills are real churn events.** Rewind/Limitless: Meta acquired Limitless (Dec 2025), stopped pendant sales, shut the Rewind app, ended EU service entirely — users burned by a product they paid for ([Fast.io review](https://fast.io/resources/limitless-ai-review-2026/)); Pocket was shut down by Mozilla, cited as motivation for Karakeep's existence ([Karakeep README](https://github.com/karakeep-app/karakeep)). Reor — a flagship local AI notes app — was archived outright ([repo](https://github.com/reorproject/reor)).
- **Local-model quality disappointment.** Reor launch feedback: related-notes "so weak it was nonsensical" ([HN](https://news.ycombinator.com/item?id=39372159)); Smart Connections v2 "It's been a mess the entire time… I'll simply ignore Smart Connections until I can install a GPU" ([#1244](https://github.com/brianpetro/obsidian-smart-connections/issues/1244), [#997](https://github.com/brianpetro/obsidian-smart-connections/issues/997)).

---

## 4. FEATURE REQUESTS — most requested across communities/tools

| Feature | Evidence |
|---|---|
| **Mobile offline access** | Karakeep #1077 "Offline cache on Mobile app" — 51 👍, open since Feb 2025, "dealbreaker" language ([issue](https://github.com/karakeep-app/karakeep/issues/1077)) |
| **Messenger capture (Telegram/WhatsApp)** | Khoj built WhatsApp first-class on cloud ([docs](https://docs.khoj.dev/clients/whatsapp/), [Flint](https://github.com/khoj-ai/flint)); a whole micro-ecosystem of DIY Telegram→Obsidian bots exists because main products don't: [Engram](https://github.com/mishablank/Engram), [bot-telegram-obsidian-capture](https://github.com/matteocervelli/bot-telegram-obsidian-capture), [agent-second-brain](https://github.com/smixs/agent-second-brain), [unified-bookmarks (Telegram+WhatsApp+n8n)](https://github.com/AbOdWs/unified-bookmarks) |
| **Email ingestion** | Karakeep #183 "Email forward link feature… one of the features I'd miss most from Readwise" — maintainer deferred to n8n ([issue](https://github.com/karakeep-app/karakeep/issues/183)); Memento builds an entire product on "email inboxes… a good proxy for all the important things that happened in your life" ([HN](https://news.ycombinator.com/item?id=48557937)) |
| **OCR for images/screenshots** | Karakeep #296 OCR search in images — "Without OCR… the hoarding images become somewhat pointless"; shipped after demand, later LLM-OCR added ([issue](https://github.com/karakeep-app/karakeep/issues/296), [PR #2442](https://github.com/karakeep-app/karakeep/pull/2442)); screenshot-to-second-brain for meetings requested in #1273 ([issue](https://github.com/karakeep-app/karakeep/issues/1273)) |
| **MCP / agent access** | Atomic praised for MCP read/write on day one ([HN](https://news.ycombinator.com/item?id=47470433)); Recall ships API & MCP as a headline feature ([pricing page](https://www.recall.it/pricing)); Limitless exposes MCP ([limitless.ai](https://www.limitless.ai/new)); Karakeep ships "LLM Agent friendly" CLI + official agent skills ([README](https://github.com/karakeep-app/karakeep)); dozens of PKM-as-MCP-server projects exist ([example](https://github.com/vishnu-vasan/mcp-knowledge-base)) |
| **Browser extension capture incl. paywalled/auth pages** | Karakeep #2814 Safari client-side capture ([issue](https://github.com/karakeep-app/karakeep/issues/2814)); Obsidian Web Clipper is the standard comparison ([VTI guide](https://vtitech.vn/cai-dat-ai-second-brain-voi-obsidian-tu-zero-den-karpathy-llm-wiki/)) |
| **RSS ingestion** | Karakeep "Auto hoarding from RSS feeds" ships in README; Atomic's own usage is RSS-first ([README](https://github.com/karakeep-app/karakeep), [HN](https://news.ycombinator.com/item?id=47470433)) |
| **Local/offline LLM support** | Smart Connections' core differentiator is offline local embeddings ([README](https://github.com/brianpetro/obsidian-smart-connections)); Khoj "chat with any local or online LLM" ([repo](https://github.com/khoj-ai/khoj/)); Reor's whole premise ([repo](https://github.com/reorproject/reor)) |
| **Export / no lock-in** | NotebookLM's biggest structural complaint: "There's no export… a walled garden" ([XDA](https://www.xda-developers.com/notebooklm-limitations/)); Mem users have "portability anxiety" because export gives text but not the retrieval graph ([dev.to](https://dev.to/pickuma/mem-review-ai-organized-notes-one-year-on-4h83)) |
| **Proactive resurfacing / digest** | The complaint "NotebookLM becomes storage with a chat interface… it refuses to connect those dots unless I explicitly open the right notebook" ([XDA](https://www.xda-developers.com/notebooklm-limitations/)) is exactly what spaced-repetition/resurfacing features claim to fix — HN commenters point to AI-driven resurfacing as "a promising approach" ([#36136179](https://news.ycombinator.com/item?id=36136179)); DIY Telegram bots implement nightly processing + daily digest ([agent-second-brain](https://github.com/smixs/agent-second-brain), [ultrathink_2b morning briefing](https://github.com/RADobson/ultrathink_2b)) |

---

## 5. WILLINGNESS TO PAY

### What consumers pay today (cloud AI knowledge tools)

| Product | Price | Source |
|---|---|---|
| Notion AI | $10/user/mo add-on retired May 2025 → Business plan $20/user/mo is now the AI entry point; usage-based credits ($10/1,000) on top | [gotnerfed tracking](https://gotnerfed.com/changes/notion-ai-2025-05-addon-removed), [Notion pricing](https://www.notion.com/pricing), [DANIAN audit](https://danian.co/articles/post/notion-pricing-pivot-audit) |
| Mem | ~$14.99/mo | [aifoss comparison table](https://aifoss.dev/blog/khoj-review-2026/) |
| Recall | Free tier; Plus $10/mo (annual); Max $38/mo | [Recall pricing](https://www.recall.it/pricing) |
| Limitless (Rewind) | Pro $19/mo; pendant $99 one-time | [TheAISelect review](https://www.theaiselect.com/en/tools/limitless-ai) |
| Obsidian Sync / Publish | $4–8/mo Sync; $8–10/mo Publish — funds Obsidian as a "100% user-supported" company | [Obsidian pricing](https://obsidian.md/pricing), [Obsidian blog](https://obsidian.md/blog/standard-plan/) |
| Smart Connections Pro | $20/mo subscription (open-source plugin with paid Pro tier) | [codeculture](https://codeculture.store/blogs/developer-culture/obsidian-ai-plugin-comparison-2025), [Starlog](https://starlog.is/articles/ai-dev-tools/brianpetro-obsidian-smart-connections) |

### Do self-hosters pay? Yes — three proven patterns

1. **Paid feature licenses on self-hosted software.** Bitwarden: self-hosting is free, but premium features on your own server require a paid cloud license ($19.80/yr; families $47.88/yr) ([Bitwarden docs](https://bitwarden.com/help/licensing-on-premise/), [blog](https://bitwarden.com/blog/bitwarden-launches-enhanced-premium-plan/)). Plex Pass $6.99/mo, lifetime raised to $749.99 — and the trend of self-hosted apps charging subscriptions is now mainstream enough to attract backlash articles, which itself proves people are paying ([XDA](https://www.xda-developers.com/self-hosted-apps-charging-subscriptions-defeats-purpose/)).
2. **Open-core / hosted-cloud pays the bills while self-host stays free.** Plausible's canonical write-up: free self-hosted edition + paid cloud of the same software; same playbook at Ghost, Discourse, Matrix ([Plausible](https://plausible.io/blog/open-source-funding)). Khoj runs this pattern (cloud app.khoj.dev funds AGPL core, [aifoss](https://aifoss.dev/blog/khoj-review-2026/)).
3. **Free for individuals, paid for teams/business.** Tailscale: "We never intend to charge money for individuals… those people bring it to work" — $160M Series C on this model ([Network World](https://www.networkworld.com/article/3958366/tailscale-secures-160-million-for-its-wireguard-based-vpn-development.html)).
- Donations alone are known-weak: "Donations may be the simplest way of raising funds but may also be a difficult method to achieve sustainable levels of funding" ([Plausible](https://plausible.io/blog/open-source-funding)); Wikipedia's survey of OSS business models notes most commercial OSS converts well below 1% of downloaders to paying ([Wikipedia](https://en.wikipedia.org/wiki/Business_models_for_open-source_software)).
- **Implication:** a self-hosted AI second brain has credible monetization via (a) Pro/license tiers, (b) optional managed hosting, (c) team/workspace paid tier — but a pure donation cup is not a plan. Also note license sensitivity: r/selfhosted users police licenses closely (Joplin's mixed licensing triggered a whole audit thread, [piefed](https://piefed.social/c/selfhosted/p/1875507/what-s-the-best-open-source-selfhostable-notion-replacement)) — Orivory's MIT license is an asset here, and AGPL competitors' licensing is a marketing wedge.

---

## 6. VIETNAMESE ANGLE (secondary)

- **Demand exists in Vietnamese.** A Vietnamese-language Obsidian second-brain framework "vietbrain" (PARA + Zettelkasten, AI agent that pings you via **Zalo/Telegram**) is published as a community gift ([repo](https://github.com/tuanminhhole/vietbrain)); multiple substantial Vietnamese guides to Obsidian + AI second brain exist ([khoaphambk](https://khoaphambk.com/obsidian-la-gi-huong-dan-xay-dung-second-brain-tu-dau-cho-nguoi-moi/), [long.vn](https://long.vn/ai/bo-nao-thu-2-obsidian-ai/), [VTI TechBlog](https://vtitech.vn/cai-dat-ai-second-brain-voi-obsidian-tu-zero-den-karpathy-llm-wiki/), [trainghiemso.vn](https://trainghiemso.vn/kinh-nghiem-khi-bat-dau-dung-obsidian/)); paid Vietnamese workshops/communities around Obsidian are being run (1ight Club, 200k VND entry, [Substack](https://the1ight.substack.com/p/mo-khoa-8-chia-se-ve-obsidian-2nd)).
- **Multilingual retrieval is a documented failure mode.** NotebookLM: "If I have a notebook with both English and Vietnamese sources, and I prompt it in Vietnamese, it heavily biases towards the Vietnamese documents… makes the tool practically useless for non-English speakers" ([Google AI forum](https://discuss.ai.google.dev/t/critical-regression-gemini-3-1-pro-update-feb-19-completely-broke-notebooklm-s-rag-grounding/126857)); the same cross-lingual embedding problem shows up in Obsidian Copilot with Chinese notes ([#1224](https://github.com/logancyang/obsidian-copilot/issues/1224)); Karakeep's OCR maintainer worried about multilingual OCR configs ([#296](https://github.com/karakeep-app/karakeep/issues/296)).
- **Gap:** none of the major tools ship Vietnamese localization or advertise Vietnamese-optimized embeddings; Recall claims 35+ languages for summaries ([Nubia](https://nubiapage.com/recall-ai/)) but that is capture-side, not retrieval-verified. A VN-language retrieval + capture surface (Telegram/Zalo bots are the culturally normal capture channel in VN, per vietbrain's design) is a low-competition wedge.

---

## Top 10 pains, ranked

| # | Pain | Evidence notes | Key sources |
|---|---|---|---|
| 1 | **Capture friction** (mobile, speed, steps) | Quoted as "the killer"/"the entire game" by multiple independent quitters; spawned whole micro-app category; NotebookLM mobile called out | [Medium Notion-quitter](https://medium.com/@lekhanshojha/notion-for-personal-use-why-i-quit-after-a-year-and-what-i-use-instead-5db6106fab82), [Kay Foxley](https://oh-kayyyy.medium.com/everyone-recommends-notion-ive-abandoned-it-three-times-ef2fcad2ef22), [Android Police](https://www.androidpolice.com/stop-using-notebooklm-as-direct-replacement-to-onenote-evernote/) |
| 2 | **Bad retrieval quality / hallucinated answers** | Seen in Copilot (#1224), Smart Connections (#305, #1287), Notion AI, NotebookLM regression thread, Reor launch feedback | [#1224](https://github.com/logancyang/obsidian-copilot/issues/1224), [Google AI forum](https://discuss.ai.google.dev/t/critical-regression-gemini-3-1-pro-update-feb-19-completely-broke-notebooklm-s-rag-grounding/126857), [HN Reor](https://news.ycombinator.com/item?id=39372159) |
| 3 | **Setup friction: Docker/networking/keys** | AnythingLLM #3656; "90% of problems are one networking mistake"; docs exist solely for this; Smart Connections API-key confusion | [#3656](https://github.com/Mintplex-Labs/anything-llm/issues/3656), [WikiWayne](https://wikiwayne.com/blog/open-webui-ollama-connection-guide), [#997](https://github.com/brianpetro/obsidian-smart-connections/issues/997) |
| 4 | **Organizing tax / dumping-ground dynamics** | "Landfill of stale notes"; "organizing tax higher than value"; Supernotes churn observation | [nuric](https://www.doc.ic.ac.uk/~nuric/posts/misc/stopped-using-notion-for-more-productivity/), [HN #46826277](https://news.ycombinator.com/item?id=46826277), [HN #36136179](https://news.ycombinator.com/item?id=36136179) |
| 5 | **Maintenance burden of self-hosting** | Khoj 1–2 h/mo updates; RAG "half a day a month"; 5–10 h/mo for local LLM stacks | [aifoss](https://aifoss.dev/blog/khoj-review-2026/), [DEV RAG guide](https://dev.to/mryadavgulshan/self-hosted-rag-a-production-pipeline-on-your-own-hardware-2a5i), [aisuperior](https://aisuperior.com/cost-of-running-local-llm/) |
| 6 | **No proactive resurfacing — data goes stale silently** | NotebookLM "amnesiac by design"; users abandon notebooks; demand for digests/briefings in DIY bots | [XDA](https://www.xda-developers.com/notebooklm-limitations/), [agent-second-brain](https://github.com/smixs/agent-second-brain), [ultrathink_2b](https://github.com/RADobson/ultrathink_2b) |
| 7 | **Connector/sync quality (paywalls, stuck states, offline)** | Onyx stuck-indexing issues; Karakeep paywall capture #2814; offline mobile "dealbreaker" #1077 (51👍) | [#2814](https://github.com/karakeep-app/karakeep/issues/2814), [#1077](https://github.com/karakeep-app/karakeep/issues/1077), [Onyx #8379](https://github.com/onyx-dot-app/onyx/issues/8379) |
| 8 | **LLM cost & hardware (API bills vs GPU economics)** | RTX 4090 ≈ $104/mo all-in; break-even math; API-key surprises in plugins | [cost calculator](https://www.kunalganglani.com/blog/local-llm-cost-breakeven), [premai comparison](https://www.premai.io/blog/self-hosted-llm-guide-setup-tools-cost-comparison-2026/) |
| 9 | **Lock-in / export / portability anxiety** | NotebookLM no export; Mem's export loses the retrieval graph; Notion proprietary format; TOS-termination fear | [XDA](https://www.xda-developers.com/notebooklm-limitations/), [dev.to Mem](https://dev.to/pickuma/mem-review-ai-organized-notes-one-year-on-4h83), [ejl.st](https://ejl.st/notion-kinda-sucks/) |
| 10 | **Trust/anxiety about agentic access + security incidents** | "Large amounts of personal data accessible, unchecked, to an AI is concerning"; AnythingLLM CVE-9.6 RCE | [HN Atomic](https://news.ycombinator.com/item?id=47470433), [DEV roundup](https://dev.to/thegatewayguy/the-local-llm-stack-in-2026-what-actually-works-ib1) |

---

## Segments table

| Segment | Size signal | Core need | Willingness to pay | Key sources |
|---|---|---|---|---|
| Self-hosters/homelabbers | r/selfhosted ~830K (+42%/yr) | Own their notes; sync that works; low-maintenance Docker | Low for licenses; real for Pro features/hosting (Plex/Bitwarden pattern) | [GummySearch](https://gummysearch.com/r/selfhosted/), [Lemmy thread](https://gammel.feddit.dk/post/55835), [XDA](https://www.xda-developers.com/self-hosted-apps-charging-subscriptions-defeats-purpose/) |
| Privacy-conscious knowledge workers | r/ObsidianMD ~359K | AI on their notes without cloud; reliable semantic search | $4–8/mo (Sync); $20/mo (Smart Connections Pro) | [GummySearch](https://gummysearch.com/r/ObsidianMD/), [Obsidian pricing](https://obsidian.md/pricing), [codeculture](https://codeculture.store/blogs/developer-culture/obsidian-ai-plugin-comparison-2025) |
| Developers / AI builders | r/LocalLLaMA ~815K; HN Show HN traction | MCP access, agent-writable memory, local models | Highest tolerance for infra spend ($1.5–4K GPU) but hate token bills | [GummySearch](https://gummysearch.com/r/LocalLLaMA/), [HN Atomic](https://news.ycombinator.com/item?id=47470433), [aisuperior](https://aisuperior.com/cost-of-running-local-llm/) |
| Students / researchers | r/notebooklm ~148K (+183%/yr); Recall "500K users" | Summarize + chat with sources; quizzes; portability | $10/mo tier is the sweet spot (Recall Plus, Notion add-on legacy) | [GummySearch](https://gummysearch.com/r/notebooklm/), [Recall pricing](https://www.recall.it/pricing), [Nubia](https://nubiapage.com/recall-ai/) |
| Small teams / families | AnythingLLM multi-user; family-space asks | Shared self-hosted knowledge with permissions; meeting notes | Per-seat like Notion Business $20, or self-host + support | [aifoss](https://aifoss.dev/blog/khoj-review-2026/), [piefed](https://piefed.social/c/selfhosted/p/1875507/what-s-the-best-open-source-selfhostable-notion-replacement), [Notion pricing](https://www.notion.com/pricing) |

---

## Key takeaways for Orivory

1. **The market pull is real and growing** — every adjacent community is compounding double-digit YoY (r/selfhosted +42%, r/LocalLLaMA +54%, r/ObsidianMD +47%, r/notebooklm +183%), and 3–4 Show HN products target this exact niche every quarter. The niche is contestable; nobody owns "self-hosted AI second brain" yet.
2. **Win on capture friction first.** The single most-documented abandonment cause is that capture takes too many steps; tools die "with a quiet last login." Ship a sub-2-second capture path: mobile share-sheet/widget, browser extension, and Telegram/Zalo/WhatsApp bots — the number of DIY Telegram→Obsidian bots proves main products underserve this.
3. **Retrieval quality is the credibility test.** Every incumbent in the pain list got burned publicly for irrelevant retrieval or confident hallucinations. Orivory's corrective-RAG + hybrid search + reranking stack should be *marketed with evidence* (retrieval evals, citations by default, "says 'I don't know' when context is insufficient") — that's a differentiated, checkable claim.
4. **Show the citations, always.** "A synthesized answer reads smoothly whether or not it pulled the right sources" is Mem's core trust complaint; Onyx/NotebookLM users value traceability. Every Orivory answer should carry clickable source provenance.
5. **Proactive digest is the differentiator incumbents don't do.** The loudest structural complaint (NotebookLM "amnesiac by design," notes going stale silently) is exactly Orivory's "on this day"/weekly themes/digest feature — make it the hero feature, not a sidebar.
6. **Default-docker must work on first try.** Setup hell (docker networking, stuck connectors, silent indexing failures) is a top-3 pain. Invest in a `docker compose up` that self-diagnoses: health checks, visible indexing progress/stats, actionable error messages. AnythingLLM ships a troubleshooting doc page just for Ollama URLs — that's a whole class of support pain you can eliminate.
7. **MCP + agent access is table stakes for the developer segment.** Ship an MCP server exposing read/write memory tools on day one; the HN reaction to Atomic's MCP-first design shows the demand explicitly.
8. **Multilingual (incl. Vietnamese) retrieval is a real, unclaimed wedge.** Cross-lingual retrieval failure is documented at NotebookLM and Obsidian Copilot; Vietnamese PKM content/communities exist and competitors have zero VN presence. bge-m3-class embeddings (multilingual, CPU-friendly) + a Telegram/Zalo capture bot are cheap bets.
9. **Price like Obsidian, not like Notion.** $4–8/mo user-supported services sync/publish fund Obsidian profitably; the $10 consumer AI tier (Recall Plus, legacy Notion add-on, Mem) is the proven individual price point; teams pay $20/seat. For self-hosters: premium license tiers (Bitwarden pattern) and optional managed hosting (Plausible/Khoj pattern) beat donations.
10. **MIT license is a marketing weapon.** r/selfhosted users audit licenses and resent Joplin's mixed licensing; several direct competitors are AGPL (Khoj, Karakeep, Reor) which blocks some commercial reuse — Orivory's permissive license is a wedge for both contributors and small businesses.
11. **Beware the graveyard dynamic: design for resurfacing, not filing.** "Second brain became a graveyard of good intentions" is the category's core psychological failure. Lean into salience/decay + time-aware recall so the product *retrieves* for users instead of asking them to organize.
12. **Make export/anti-lock-in loud.** NotebookLM's no-export and Mem's portability anxiety are churn stories; "your notes are plain Markdown, leave anytime" is both a trust builder and a conversion lever for refugees from Notion.

---

## Appendix: strongest individual sources

1. **Reor Show HN thread** — candid local-RAG quality critique from builders who tried it: https://news.ycombinator.com/item?id=39372159
2. **NotebookLM RAG regression thread (Google AI Developers Forum)** — retrieval failure → hallucination, multilingual bias incl. Vietnamese: https://discuss.ai.google.dev/t/critical-regression-gemini-3-1-pro-update-feb-19-completely-broke-notebooklm-s-rag-grounding/126857
3. **Karakeep issue #1077 (offline mobile cache, 51 👍)** — the clearest single feature-demand datapoint: https://github.com/karakeep-app/karakeep/issues/1077
