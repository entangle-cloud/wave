import { editorViewCtx, parserCtx } from "@milkdown/kit/core";
import { computeDocDiff } from "@milkdown/plugin-diff";
import type { EditorView } from "@milkdown/prose/view";
export function patchMarkdown(
  editor: { action: (action: (ctx: any) => unknown) => unknown },
  newMarkdown: string,
): boolean {
  return editor.action((ctx) => {
    const view: EditorView = ctx.get(editorViewCtx);
    const parser = ctx.get(parserCtx);
    const oldDoc = view.state.doc;
    const newDoc = parser(newMarkdown);
    if (oldDoc.eq(newDoc)) {
      return false;
    }
    const changes = computeDocDiff(oldDoc, newDoc);
    if (changes.length === 0) {
      return false;
    }
    let tr = view.state.tr;
    for (let i = changes.length - 1; i >= 0; i--) {
      const change = changes[i]!;
      tr = tr.replace(
        change.fromA,
        change.toA,
        newDoc.slice(change.fromB, change.toB),
      );
    }
    if (!tr.docChanged) {
      return false;
    }
    tr.setSelection(view.state.selection.map(tr.doc, tr.mapping));
    view.dispatch(tr);
    return true;
  }) as boolean;
}
