def format_review_comment(result: dict, pr_title: str) -> str:
    score = result["score"]
    total = result["total_issues"]
    counts = result["severity_counts"]
    issues = result["issues"]

    score_emoji = "🟢" if score >= 8 else "🟡" if score >= 6 else "🔴"
    lines = [
        "## 🔍 CodeSage AI Review",
        "",
        f"**PR:** {pr_title}",
        "",
        f"### {score_emoji} Overall Score: `{score}/10`",
        "",
        "| Metric | Count |",
        "|--------|-------|",
        f"| 🔴 Critical | {counts.get('critical', 0)} |",
        f"| 🟠 High | {counts.get('high', 0)} |",
        f"| 🟡 Medium | {counts.get('medium', 0)} |",
        f"| 🟢 Low | {counts.get('low', 0)} |",
        f"| ℹ️ Info | {counts.get('info', 0)} |",
        f"| **Total** | **{total}** |",
        "",
    ]

    if issues:
        lines.append("### Issues Found")
        lines.append("")

        categories = {}
        for issue in issues:
            cat = issue.get("category", "general")
            categories.setdefault(cat, []).append(issue)

        cat_icons = {
            "security": "🔒 Security",
            "performance": "⚡ Performance",
            "quality": "✨ Quality",
            "testing": "🧪 Testing",
        }

        for cat, cat_issues in categories.items():
            lines.append(f"#### {cat_icons.get(cat, cat.capitalize())}")
            lines.append("")
            for issue in cat_issues[:5]:  # max 5 per category to keep comment readable
                sev = issue["severity"].upper()
                line_ref = f" (line {issue['line_number']})" if issue.get("line_number") else ""
                lines.append(f"**[{sev}]** `{issue['file_name']}`{line_ref}")
                lines.append(f"- **Issue:** {issue['issue']}")
                lines.append(f"- **Suggestion:** {issue.get('suggestion', 'N/A')}")
                if issue.get("code_snippet"):
                    lines.append(f"```\n{issue['code_snippet']}\n```")
                lines.append("")

    lines += [
        "---",
        "*Reviewed by [CodeSage](https://github.com) — AI-powered code review*",
    ]
    return "\n".join(lines)
