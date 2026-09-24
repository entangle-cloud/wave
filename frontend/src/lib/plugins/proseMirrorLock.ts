import { $prose } from "@milkdown/utils";
import { Plugin, PluginKey } from "@milkdown/prose/state";

export const protectSectionPlugin = $prose(() => {
  return new Plugin({
    key: new PluginKey("PROTECT_SECTION"),
    filterTransaction(tr, state) {
      if (tr.docChanged) {
        let isEditingLockedSection = false;

        tr.steps.forEach((step) => {
          step.getMap().forEach((oldStart, oldEnd) => {
            state.doc.nodesBetween(oldStart, oldEnd, (node) => {
              // Checks attribute on the fly when user edits
              if (node.attrs?.readOnly === true) {
                isEditingLockedSection = true;
              }
            });
          });
        });

        if (isEditingLockedSection) return false;
      }
      return true;
    },
  });
});
