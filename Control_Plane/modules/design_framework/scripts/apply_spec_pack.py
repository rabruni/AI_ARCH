import argparse
import os
import shutil

def apply_spec_pack(target_dir, force=False):
    """Copies the spec pack templates to the target directory."""
    source_dir = os.path.join(os.path.dirname(__file__), '..', 'templates', 'spec_pack')
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    print(f"Applying spec pack to: {target_dir}")

    for item in os.listdir(source_dir):
        source_item = os.path.join(source_dir, item)
        target_item = os.path.join(target_dir, item)

        if os.path.isdir(source_item):
            if not os.path.exists(target_item):
                os.makedirs(target_item)
            for sub_item in os.listdir(source_item):
                source_sub_item = os.path.join(source_item, sub_item)
                target_sub_item = os.path.join(target_item, sub_item)
                if os.path.exists(target_sub_item) and not force:
                    print(f"Skipped (exists): {target_sub_item}")
                else:
                    shutil.copy2(source_sub_item, target_sub_item)
                    print(f"Created: {target_sub_item}")
        else:
            if os.path.exists(target_item) and not force:
                print(f"Skipped (exists): {target_item}")
            else:
                shutil.copy2(source_item, target_item)
                print(f"Created: {target_item}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apply the Spec Pack + Gates templates.")
    parser.add_argument("--target", required=True, help="The directory to copy the templates to.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files.")
    args = parser.parse_args()

    apply_spec_pack(args.target, args.force)
