# Companion tools

[Home](README.md) · [Skill catalog](CATALOG.md) · [Sources and licenses](SOURCES.md)

These are executable tools and frameworks, counted separately from agent skills. Their README/source overviews were inspected; this repository has not installed or run them. Links point to the recorded revision.

**17 tools and frameworks in 7 groups.** See [start here](docs/start-here.md) for task-oriented selections.

| Group | Tools |
| --- | ---: |
| [Visual workflows](#visual-workflows) | 3 |
| [Chat workspaces](#chat-workspaces) | 2 |
| [Document ingestion](#document-ingestion) | 5 |
| [Image workflows](#image-workflows) | 2 |
| [Coding agents](#coding-agents) | 3 |
| [AI application SDKs](#ai-application-sdks) | 1 |
| [API testing](#api-testing) | 1 |

<a id="visual-workflows"></a>

## Visual workflows

| Tool | ใช้ทำอะไร | ต้องมี / ข้อจำกัด |
| --- | --- | --- |
| [Dify](https://github.com/langgenius/dify/tree/8a43387fe4934506f4168943556ad03362d82ad9) | สร้าง LLM apps, workflow และ RAG ผ่าน visual workspace | Docker Compose, backing services และ model/embedding endpoints. Modified Apache license มีข้อกำหนดเพิ่ม; อ่านเงื่อนไข multi-tenant และ branding ก่อนนำไปทำบริการ |
| [n8n](https://github.com/n8n-io/n8n/tree/004dea2c9d8ab1b2d28de977073911a41d7ba167) | ต่อ workflows ระหว่าง AI, webhooks, messaging และบริการอื่น | Node/Docker, persistent storage และ integration credentials. Sustainable Use License และ enterprise scope แยก; source-available ไม่เท่ากับ permissive license |
| [FastGPT](https://github.com/labring/FastGPT/tree/ce796cea84abb5a3708a51c2a5851cbf9d7d6441) | สร้าง knowledge-based chat และ visual AI workflows | Self-hosted platform services และ model/embedding providers. Custom FastGPT license เพิ่มเงื่อนไข SaaS/branding; ไม่ติดป้ายเป็น Apache แบบไม่มีเงื่อนไข |

<a id="chat-workspaces"></a>

## Chat workspaces

| Tool | ใช้ทำอะไร | ต้องมี / ข้อจำกัด |
| --- | --- | --- |
| [Open WebUI](https://github.com/open-webui/open-webui/tree/b0e6098e940942281d9c83f3529ea117287a3a22) | สร้าง self-hosted chat UI ที่ต่อ local models หรือ compatible APIs | Python/Docker และ inference/embedding endpoints. Open WebUI License มีเงื่อนไข branding; offline mode ต้องตรวจ dependencies และ provider routes |
| [AnythingLLM](https://github.com/Mintplex-Labs/anything-llm/tree/728586d76c843ed25cb7a27c7403f4b79bd960c8) | ใช้ workspace chat, documents, RAG และ Agents บน desktop/server | Desktop/Docker หรือ Node stack และ model/embedding backend. Desktop กับ Docker มี feature scope ต่างกัน; ตรวจ ingestion และ outbound provider calls |

<a id="document-ingestion"></a>

## Document ingestion

| Tool | ใช้ทำอะไร | ต้องมี / ข้อจำกัด |
| --- | --- | --- |
| [Crawl4AI](https://github.com/unclecode/crawl4ai/tree/cae74b203a33994f7e13b9052c3b0d5c93daa0e6) | แปลงเว็บเป็น Markdown หรือ structured data สำหรับ Agent/RAG | Python/browser หรือ Docker; hosted API เป็นอีกตัวเลือก. แยก self-hosted crawler จาก Cloud endpoints; ตั้ง crawl scope และ budget |
| [Docling](https://github.com/docling-project/docling/tree/da1eda8a6b4ef62691eee6e72ced4891a30e654c) | แยก layout, tables, OCR และ export เอกสารเป็นข้อมูลสำหรับ AI | Python และ parser/OCR/model dependencies ตาม format. Model artifacts อาจมีสิทธิ์แยก; ตรวจ tables, reading order และ citation locators กับ fixture จริง |
| [MarkItDown](https://github.com/microsoft/markitdown/tree/ed178952a6672abdfd35b5f9e76a80b6cefc086e) | แปลงเอกสารหลายชนิดเป็น Markdown สำหรับ text-analysis pipelines | Python และ format-specific dependencies. Converter ใช้สิทธิ์ I/O ของ process; image captioning/audio บางงานอาจเรียกบริการภายนอก |
| [MinerU](https://github.com/opendatalab/MinerU/tree/06c3481e9bf534e8d57a3f980e1f4c3cbd79f745) | parse เอกสารซับซ้อน ตาราง สูตร และ scanned pages เป็น Markdown/JSON | Parser/runtime และ hardware/model backend ตาม mode. MinerU license เพิ่มเงื่อนไขจาก Apache; ตรวจ API รุ่นจริงและข้อกำหนดของ models |
| [Firecrawl](https://github.com/firecrawl/firecrawl/tree/32fa6f6273daecc9675d41dc2dab44c61e8cc500) | ค้น scrape crawl และแปลงเว็บ/เอกสารเป็น context สำหรับ Agent | Hosted API หรือ self-hosted services ตามการใช้งาน. ใช้ canonical firecrawl/firecrawl; AGPL source และ hosted features/terms ต้องตรวจแยก |

<a id="image-workflows"></a>

## Image workflows

| Tool | ใช้ทำอะไร | ต้องมี / ข้อจำกัด |
| --- | --- | --- |
| [ComfyUI](https://github.com/Comfy-Org/ComfyUI/tree/4d64a8bc072b81c9b47321789b4d83fb7348ae2a) | ประกอบ image/video/audio generation ผ่าน node-graph workflows | Model artifacts และ compute ตาม workflow. GPL ของโปรแกรมแยกจาก model/custom-node licenses; custom nodes เป็น code ที่ต้องตรวจเอง |
| [Diffusers](https://github.com/huggingface/diffusers/tree/f598e6e6a99528858b962c1399c45b59a6c25484) | สร้าง diffusion pipelines และปรับ schedulers/models ใน Python | Python/PyTorch, model files และ compatible hardware. Library Apache-2.0 ไม่ได้ครอบคลุม model weights ทุกตัว; GPU/VRAM ขึ้นกับ pipeline |

<a id="coding-agents"></a>

## Coding agents

| Tool | ใช้ทำอะไร | ต้องมี / ข้อจำกัด |
| --- | --- | --- |
| [OpenHands](https://github.com/OpenHands/OpenHands/tree/7b5aa9eb60bdef7d832743c12cabd537b44b8a41) | จัด coding agents และ automations ผ่าน self-hosted Agent Canvas | App/runtime backend, model access และ sandbox ตาม setup. Agent สามารถเปลี่ยนไฟล์และเรียก tools; จำกัด repository/workspace ตามงาน |
| [Aider](https://github.com/Aider-AI/aider/tree/5dc9490bb35f9729ef2c95d00a19ccd30c26339c) | ทำ AI pair programming ใน terminal พร้อม repo map และ Git integration | Python, Git และ LLM provider/local endpoint. ตรวจ auto-commit/test behavior; model examples ใน README ไม่ใช่คำแนะนำรุ่นปัจจุบันของคลัง |
| [OpenCode](https://github.com/anomalyco/opencode/tree/070b980c0b17487dcb94f381cc2eb03953dadb86) | ใช้ coding agent แบบ terminal/desktop พร้อม build และ plan modes | CLI/desktop runtime และ provider configuration. MIT ของ client ไม่รับรองราคา โควตา หรือเงื่อนไขโมเดลของ provider |

<a id="ai-application-sdks"></a>

## AI application SDKs

| Tool | ใช้ทำอะไร | ต้องมี / ข้อจำกัด |
| --- | --- | --- |
| [Vercel AI SDK](https://github.com/vercel/ai/tree/70e45d5878494be4b66e325187f865951025059e) | ต่อ text/streaming, structured outputs, tools และ UI สำหรับแอป TypeScript | Node 22+ ตาม README ที่อ่าน, provider adapter หรือ gateway และ UI integration ตามงาน. String model ID อาจเลือก Vercel AI Gateway; adapter โดยตรงเป็นอีกเส้นทาง ต้องบันทึก provider/billing route |

<a id="api-testing"></a>

## API testing

| Tool | ใช้ทำอะไร | ต้องมี / ข้อจำกัด |
| --- | --- | --- |
| [Bruno](https://github.com/usebruno/bruno/tree/60d7517d0545ef82c032c10dcbb6a3c815d246cf) | เก็บ API request collections เป็นไฟล์และรันทดสอบผ่าน desktop/CLI | Desktop app หรือ CLI, API test environment และ credentials ที่แยกจาก collection. Collection อยู่ local และใช้ Git ได้; HTTP requests ยังติดต่อ API เป้าหมาย และ paid editions มี feature scope แยก |
