#!/usr/bin/env python3
"""
Initialize project documentation from templates.
Usage:
  python scripts/init_docs.py --project "My Project" --owner "Your Name" --template software_mvp
If flags are omitted, you'll be prompted.
"""
import argparse, datetime, yaml, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
CONFIG = ROOT / "config"
TEMPLATES = CONFIG / "templates"

def fill(text:str, mapping:dict)->str:
    for k,v in mapping.items():
        text = text.replace("{{"+k+"}}", v)
    return text

def load_template_registry():
    """Load available project templates."""
    registry_path = TEMPLATES / "registry.yaml"
    if not registry_path.exists():
        return {"templates": {"software_mvp": {"name": "Software MVP", "description": "Default template"}}}
    
    try:
        with open(registry_path, 'r') as f:
            import yaml
            return yaml.safe_load(f)
    except ImportError:
        print("Warning: PyYAML not installed. Using default template.")
        return {"templates": {"software_mvp": {"name": "Software MVP", "description": "Default template"}}}

def select_template():
    """Interactive template selection."""
    try:
        registry = load_template_registry()
        templates = registry.get("templates", {})
        
        print("\nAvailable project templates:")
        for key, template in templates.items():
            print(f"  {key}: {template['name']} - {template['description']}")
        
        print(f"\nUse cases:")
        for key, template in templates.items():
            if 'use_cases' in template:
                print(f"  {template['name']}: {', '.join(template['use_cases'][:3])}")
        
        default = registry.get("default_template", "software_mvp")
        choice = input(f"\nSelect template [{default}]: ").strip() or default
        
        if choice in templates:
            return choice
        else:
            print(f"Unknown template '{choice}', using default: {default}")
            return default
    except Exception as e:
        print(f"Error loading templates: {e}")
        return "software_mvp"

def main():
    ap = argparse.ArgumentParser(description="Initialize project documentation from templates")
    ap.add_argument("--project", help="Project name")
    ap.add_argument("--owner", help="Owner name")
    ap.add_argument("--date", help="ISO date YYYY-MM-DD (default: today)")
    ap.add_argument("--template", help="Project template (default: interactive selection)")
    ap.add_argument("--force", action="store_true", help="Overwrite existing docs")
    ap.add_argument("--list-templates", action="store_true", help="List available templates and exit")
    args = ap.parse_args()

    # Handle template listing
    if args.list_templates:
        registry = load_template_registry()
        templates = registry.get("templates", {})
        print("Available templates:")
        for key, template in templates.items():
            print(f"  {key}: {template['name']} - {template['description']}")
        return

    # Get project info
    proj = args.project or input("Project name: ").strip() or "LLM Council Audit & Consensus Platform"
    owner = args.owner or input("Owner: ").strip() or "Owner"
    date = args.date or datetime.date.today().isoformat()
    template = args.template or select_template()

    mapping = {"PROJECT_NAME": proj, "OWNER": owner, "DATE": date}
    
    print(f"\nInitializing project: {proj}")
    print(f"Owner: {owner}")  
    print(f"Date: {date}")
    print(f"Template: {template}")
    
    # Create standardized project config (project_config.yaml)
    project_config = DOCS.parent / "project_config.yaml"
    registry_loaded = load_template_registry()
    templates_section = {}
    if isinstance(registry_loaded, dict):
        ts = registry_loaded.get("templates")
        if isinstance(ts, dict):
            templates_section = {str(k): v for k, v in ts.items()}
    template_entry = templates_section.get(str(template), {})
    template_cfg_name = template_entry.get("config_file", f"{template}.yaml")
    template_config = TEMPLATES / template_cfg_name
    if template_config.exists():
        if not project_config.exists() or args.force:
            shutil.copy2(template_config, project_config)
            print(f"Copied template config to {project_config.name}")
        else:
            print(f"Config {project_config.name} already exists (use --force to overwrite)")
    else:
        print(f"Warning: template config {template_cfg_name} not found; skipping config copy")

    DOCS.mkdir(parents=True, exist_ok=True)
    doc_list = [
        "RESEARCH_BRIEF.md",
        "MARKET_SCAN.md",
        "VISION.md",
        "PRD.md",
        "ARCHITECTURE.md",
        "IMPLEMENTATION_PLAN.md",
        "AUDITOR_SCHEMA.md",
        "HUMAN_REVIEW_INTERFACE.md",
    ]
    for name in doc_list:
        p = DOCS / name
        if not p.exists():
            # Create empty placeholder if missing so workflow stays intact
            p.write_text(f"# {name}\n\n(Initialize content)\n", encoding="utf-8")
            print(f"Created placeholder {p}")
        txt = p.read_text(encoding="utf-8")
        out = fill(txt, mapping)
        if out != txt:
            p.write_text(out, encoding="utf-8")
            print(f"Updated tokens in {p}")
    
    # Update index title with project name
    readme = DOCS.parent / "README.md"
    if readme.exists():
        content = readme.read_text(encoding="utf-8")
        content = content.replace("LLM Council Audit & Consensus Platform", proj)
        readme.write_text(content, encoding="utf-8")
        print(f"Updated {readme}")
    
    print(f"\n✅ Project '{proj}' initialized successfully!")
    print(f"📁 Documentation: {DOCS}")
    print(f"⚙️  Configuration: {project_config if project_config.exists() else 'NONE'}")
    print(f"\nNext steps:")
    print(f"1. Review and customize project_config.yaml (template: {template_cfg_name})")
    print(f"2. Fill out {DOCS / 'RESEARCH_BRIEF.md'}")
    print(f"3. (When implemented) run: python audit.py {DOCS} --stage research_brief --interactive")
if __name__ == "__main__":
    main()
