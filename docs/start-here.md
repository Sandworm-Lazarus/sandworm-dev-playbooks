# Start here: Dev Playbooks

[Home](../README.md) · [Tools](../TOOLS.md) · [Sources](../SOURCES.md)

Select a task, inspect the complete pinned package, then try a bounded synthetic fixture. These are reading paths and prototype ideas, not tested integrations.

## Work on a codebase

| Project | ใช้ทำอะไร | Evidence to collect |
| --- | --- | --- |
| [OpenHands](https://github.com/OpenHands/OpenHands/tree/7b5aa9eb60bdef7d832743c12cabd537b44b8a41) | จัด coding agents และ automations ผ่าน self-hosted Agent Canvas | Version, configuration, one task result, failure behavior and data/permission boundaries |
| [Aider](https://github.com/Aider-AI/aider/tree/5dc9490bb35f9729ef2c95d00a19ccd30c26339c) | ทำ AI pair programming ใน terminal พร้อม repo map และ Git integration | Version, configuration, one task result, failure behavior and data/permission boundaries |
| [OpenCode](https://github.com/anomalyco/opencode/tree/070b980c0b17487dcb94f381cc2eb03953dadb86) | ใช้ coding agent แบบ terminal/desktop พร้อม build และ plan modes | Version, configuration, one task result, failure behavior and data/permission boundaries |

## Build repeatable workflows

| Project | ใช้ทำอะไร | Evidence to collect |
| --- | --- | --- |
| [Dify](https://github.com/langgenius/dify/tree/8a43387fe4934506f4168943556ad03362d82ad9) | สร้าง LLM apps, workflow และ RAG ผ่าน visual workspace | Version, configuration, one task result, failure behavior and data/permission boundaries |
| [n8n](https://github.com/n8n-io/n8n/tree/004dea2c9d8ab1b2d28de977073911a41d7ba167) | ต่อ workflows ระหว่าง AI, webhooks, messaging และบริการอื่น | Version, configuration, one task result, failure behavior and data/permission boundaries |
| [FastGPT](https://github.com/labring/FastGPT/tree/ce796cea84abb5a3708a51c2a5851cbf9d7d6441) | สร้าง knowledge-based chat และ visual AI workflows | Version, configuration, one task result, failure behavior and data/permission boundaries |

## Prepare technical context

| Project | ใช้ทำอะไร | Evidence to collect |
| --- | --- | --- |
| [Open WebUI](https://github.com/open-webui/open-webui/tree/b0e6098e940942281d9c83f3529ea117287a3a22) | สร้าง self-hosted chat UI ที่ต่อ local models หรือ compatible APIs | Version, configuration, one task result, failure behavior and data/permission boundaries |
| [AnythingLLM](https://github.com/Mintplex-Labs/anything-llm/tree/728586d76c843ed25cb7a27c7403f4b79bd960c8) | ใช้ workspace chat, documents, RAG และ Agents บน desktop/server | Version, configuration, one task result, failure behavior and data/permission boundaries |
| [Crawl4AI](https://github.com/unclecode/crawl4ai/tree/cae74b203a33994f7e13b9052c3b0d5c93daa0e6) | แปลงเว็บเป็น Markdown หรือ structured data สำหรับ Agent/RAG | Version, configuration, one task result, failure behavior and data/permission boundaries |
| [Docling](https://github.com/docling-project/docling/tree/da1eda8a6b4ef62691eee6e72ced4891a30e654c) | แยก layout, tables, OCR และ export เอกสารเป็นข้อมูลสำหรับ AI | Version, configuration, one task result, failure behavior and data/permission boundaries |
| [MarkItDown](https://github.com/microsoft/markitdown/tree/ed178952a6672abdfd35b5f9e76a80b6cefc086e) | แปลงเอกสารหลายชนิดเป็น Markdown สำหรับ text-analysis pipelines | Version, configuration, one task result, failure behavior and data/permission boundaries |
| [MinerU](https://github.com/opendatalab/MinerU/tree/06c3481e9bf534e8d57a3f980e1f4c3cbd79f745) | parse เอกสารซับซ้อน ตาราง สูตร และ scanned pages เป็น Markdown/JSON | Version, configuration, one task result, failure behavior and data/permission boundaries |

## Explore creative workflows

| Project | ใช้ทำอะไร | Evidence to collect |
| --- | --- | --- |
| [ComfyUI](https://github.com/Comfy-Org/ComfyUI/tree/4d64a8bc072b81c9b47321789b4d83fb7348ae2a) | ประกอบ image/video/audio generation ผ่าน node-graph workflows | Version, configuration, one task result, failure behavior and data/permission boundaries |
| [Diffusers](https://github.com/huggingface/diffusers/tree/f598e6e6a99528858b962c1399c45b59a6c25484) | สร้าง diffusion pipelines และปรับ schedulers/models ใน Python | Version, configuration, one task result, failure behavior and data/permission boundaries |

## Skill starting points

| Entry | Task | Review |
| --- | --- | --- |
| [property-based-testing](https://github.com/trailofbits/skills/blob/e4dd0bb5b15535f7c5a0834187dffba6ac37e4ff/plugins/property-based-testing/skills/property-based-testing/SKILL.md) | ออกแบบ invariant และสุ่มอินพุตเพื่อหา counterexample | entry-reviewed |
| [systematic-debugging](https://github.com/obra/superpowers/blob/22f0b463e7a5e579904dd6211a520321035526f7/skills/systematic-debugging/SKILL.md) | หาต้นเหตุจากหลักฐานและทดลองสมมติฐานก่อนแก้โค้ด | entry-reviewed |
| [verification-before-completion](https://github.com/obra/superpowers/blob/22f0b463e7a5e579904dd6211a520321035526f7/skills/verification-before-completion/SKILL.md) | กำหนดหลักฐานที่ต้องเห็นก่อนรายงานว่างานเสร็จหรือเทสต์ผ่าน | entry-reviewed |
| [cloudflare](https://github.com/cloudflare/skills/blob/cbf893b954222276bf1af57e5f23379231e0efb9/skills/cloudflare/SKILL.md) | เลือกบริการ Cloudflare ให้ตรงกับ API, AI, storage, networking และ security | entry-overview |
| [durable-objects](https://github.com/cloudflare/skills/blob/cbf893b954222276bf1af57e5f23379231e0efb9/skills/durable-objects/SKILL.md) | ออกแบบ persistent state และ coordination ด้วย Durable Objects | entry-overview |
| [gateway-workers](https://github.com/cloudflare/skills/blob/cbf893b954222276bf1af57e5f23379231e0efb9/skills/gateway-workers/SKILL.md) | เขียน Worker ที่ประมวลผล HTTP traffic ผ่าน Gateway Forward policies | entry-overview |
| [web-perf](https://github.com/cloudflare/skills/blob/cbf893b954222276bf1af57e5f23379231e0efb9/skills/web-perf/SKILL.md) | วิเคราะห์โหลดหน้าเว็บ Core Web Vitals, network และ performance traces | entry-overview |
| [vercel-composition-patterns](https://github.com/vercel-labs/agent-skills/blob/1a2c79d4e6c4a2283dc2c614b6538cbe1ed5ca62/skills/composition-patterns/SKILL.md) | ปรับ React component API ด้วย composition และ compound components | entry-overview |
| [vercel-react-best-practices](https://github.com/vercel-labs/agent-skills/blob/1a2c79d4e6c4a2283dc2c614b6538cbe1ed5ca62/skills/react-best-practices/SKILL.md) | ลด waterfalls, bundle และการ render ที่ไม่จำเป็นใน React/Next.js | entry-overview |
