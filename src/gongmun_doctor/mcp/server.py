"""Local MCP server scaffold for Gongmun Doctor."""

from __future__ import annotations

from dataclasses import asdict

from mcp.server.fastmcp import FastMCP

from gongmun_doctor.mcp.services import GongmunDoctorMcpService


def create_mcp_server() -> FastMCP:
    """Create the local stdio MCP server."""
    service = GongmunDoctorMcpService()
    mcp = FastMCP(
        "Gongmun Doctor",
        instructions=(
            "Use this server for local Korean official-document correction, "
            "stored report retrieval, rule discovery, and administrative "
            "template discovery/rendering. Default to local-only file paths "
            "and avoid any cloud or network assumptions."
        ),
        json_response=True,
    )

    @mcp.tool()
    def get_server_info() -> dict:
        """Describe the currently exposed MCP surface and deferred areas."""
        return asdict(service.get_server_info())

    @mcp.tool()
    def correct_document(
        file_path: str,
        dry_run: bool = False,
        report: bool = False,
    ) -> dict:
        """Correct one local HWPX/HWP document and optionally write a markdown report."""
        return asdict(
            service.correct_document(
                file_path=file_path,
                dry_run=dry_run,
                report=report,
            )
        )

    @mcp.tool()
    def list_rules(layer: str | None = None) -> list[dict]:
        """List bundled correction rules, optionally filtered by layer."""
        return [asdict(rule) for rule in service.list_rules(layer=layer)]

    @mcp.tool()
    def get_correction_report(file_path: str) -> dict:
        """Read a previously generated markdown correction report."""
        return asdict(service.get_correction_report(file_path=file_path))

    @mcp.tool()
    def correct_documents_in_folder(
        folder_path: str,
        dry_run: bool = False,
        report: bool = False,
        recursive: bool = False,
    ) -> dict:
        """Correct every local HWPX/HWP document in a folder."""
        return asdict(
            service.correct_documents_in_folder(
                folder_path=folder_path,
                dry_run=dry_run,
                report=report,
                recursive=recursive,
            )
        )

    @mcp.tool()
    def preview_text_corrections(
        text: str,
        layers: list[str] | None = None,
    ) -> dict:
        """Preview rule-based corrections for plain text without touching files."""
        return asdict(service.preview_text_corrections(text=text, layers=layers))

    @mcp.tool()
    def list_document_templates(category: str | None = None) -> list[dict]:
        """List bundled administrative templates, optionally filtered by category."""
        return [asdict(template) for template in service.list_templates(category=category)]

    @mcp.tool()
    def match_document_templates(query: str) -> list[dict]:
        """Return templates whose trigger keywords match the query."""
        return [asdict(match) for match in service.match_templates(query=query)]

    @mcp.tool()
    def get_template_variables(template_id: str) -> list[dict]:
        """Show which variables are required to render a template."""
        return [
            asdict(variable)
            for variable in service.get_template_variables(template_id=template_id)
        ]

    @mcp.tool()
    def render_document_template(
        template_id: str,
        values: dict[str, str],
    ) -> dict:
        """Render a template with partial or complete variable values."""
        return asdict(service.render_template(template_id=template_id, values=values))

    return mcp


def main() -> None:
    """Run the local MCP server over stdio."""
    create_mcp_server().run(transport="stdio")


if __name__ == "__main__":
    main()
