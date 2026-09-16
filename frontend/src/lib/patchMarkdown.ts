import { editorViewCtx, parserCtx } from "@milkdown/kit/core";
import { replaceAll } from "@milkdown/utils";
import { computeDocDiff } from "@milkdown/plugin-diff";
import type { EditorView } from "@milkdown/prose/view";

/**
 * Full document swap for route switches (completely different document).
 * Uses `replaceAll(md, true)` which does a single parse + `view.updateState`
 * instead of `computeDocDiff` + many `tr.replace` steps. Cheaper when old and
 * new docs share little content (the common route-switch case).
 * Caller must already guarantee `newMarkdown` differs (string compare) —
 * no equality parse is done here to avoid double work.
 */
export function replaceMarkdown(
  editor: { action: (action: (ctx: any) => unknown) => unknown },
  newMarkdown: string,
): boolean {
  return editor.action(replaceAll(newMarkdown, true)) as unknown as boolean;
}
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


type DiffChange = ReturnType<typeof computeDocDiff>[number];

const yieldToBrowser = () =>
  new Promise<void>((resolve) => requestAnimationFrame(() => resolve()));

/**
 * Same diff as `patchMarkdown`, but dispatches each hunk as its own
 * transaction instead of bundling them into one, yielding to the browser
 * between dispatches once the diff is large.
 *
 * Safe to split across ticks: hunks never overlap and are applied
 * high-to-low, so a hunk's fromA/toA stays valid in the *current* doc
 * after earlier (higher-position) hunks have landed — an edit above a
 * position never shifts anything below it.
 *
 * `shouldContinue` lets the caller bail mid-chunk if a newer refresh
 * has superseded this one (mirrors the `generation` guard in Editor.svelte).
 */
export async function patchMarkdownChunked(
  editor: { action: (action: (ctx: any) => unknown) => unknown },
  newMarkdown: string,
  { chunkSize = 1, shouldContinue = () => true }: { chunkSize?: number; shouldContinue?: () => boolean } = {},
): Promise<boolean> {
  const setup = editor.action((ctx) => {
    const view: EditorView = ctx.get(editorViewCtx);
    const parser = ctx.get(parserCtx);
    const oldDoc = view.state.doc;
    const newDoc = parser(newMarkdown);
    if (oldDoc.eq(newDoc)) return null;
    const changes = computeDocDiff(oldDoc, newDoc);
    return changes.length ? { view, newDoc, changes } : null;
  }) as { view: EditorView; newDoc: any; changes: DiffChange[] } | null;

  if (!setup) return false;
  const { view, newDoc, changes } = setup;

  const applyBatch = (batch: DiffChange[]) => {
    let tr = view.state.tr;
    for (let j = batch.length - 1; j >= 0; j--) {
      const c = batch[j]!;
      tr = tr.replace(c.fromA, c.toA, newDoc.slice(c.fromB, c.toB));
    }
    if (!tr.docChanged) return;
    tr.setSelection(view.state.selection.map(tr.doc, tr.mapping));
    view.dispatch(tr);
  };

  if (changes.length <= chunkSize) {
    applyBatch(changes);
    return true;
  }

  for (let i = changes.length - 1; i >= 0 && shouldContinue(); i -= chunkSize) {
    applyBatch(changes.slice(Math.max(0, i - chunkSize + 1), i + 1));
    await yieldToBrowser();
  }
  return true;
}