---
max_turns: 2
allowed_tools: [Read, Glob, Grep, Skill]
description: An off-topic coding request must not trigger any plugin skill
expected_outcome: Claude answers directly and never calls the Skill tool
---

напиши регулярку, которая проверяет российский номер телефона в формате +7 XXX XXX-XX-XX
