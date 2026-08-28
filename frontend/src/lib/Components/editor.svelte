<script lang="ts">
  // ---------------------------------------------------------------------------
  // Imports
// -----------------------------------------------------------------------------
  import { editorViewCtx } from "@milkdown/core";
  import {replaceAll} from "@milkdown/utils"
  import { Crepe } from "@milkdown/crepe";
  import type { Node as PMNode } from "@milkdown/prose/model";
  import "@milkdown/crepe/theme/common/style.css";
  import "@milkdown/crepe/theme/frame.css";
  import { protectSectionPlugin } from "../plugins/proseMirrorLock";
  import { editorTitle, editorContent } from "../../store/editorStore.svelte";

  /**
   * Collaborative document editor component using Milkdown/Crepe.
   *
   * Provides section-based editing with locking capabilities for real-time
   * collaboration.
   *
   * Features:
   * - Markdown editing with Crepe (Milkdown wrapper)
   * - Section extraction based on headings
   * - Section locking/unlocking for concurrent editing control
   * - Content replacement per section
   * - Export to JSON/Markdown
   */

  // ---------------------------------------------------------------------------
  // Types
  // ---------------------------------------------------------------------------

  /** A single block of content that belongs to a section (under a heading). */
  type Content = {
    type: string;
    text: string | undefined;
    size: number;
    parent: string;
  };

  /** A logical document section, starting at a heading node. */
  type Section = {
    id: string;
    text?: string;
    content: Content[];
    level: number;
  };

  // ---------------------------------------------------------------------------
  // Component state
  // ---------------------------------------------------------------------------
  
  let {content= null} :{content?: string | null} = $props()

  /** Holds the Crepe editor instance once initialized */
  let crepeInstance: null | Crepe = $state<Crepe | null>(null);

  /** Default markdown content used to seed the editor on mount. */
  const DEFAULT_CONTENT = "#";

  /** Placeholder text shown when the document is empty. */
  const PLACEHOLDER_TEXT = "Start typing...";

  // ---------------------------------------------------------------------------
  // Internal helpers
  // ---------------------------------------------------------------------------

  /**
   * Retrieves the ProseMirror document node tree from the editor.
   * @returns The current document node, or undefined if not initialized.
   */
  const getDoc = (): PMNode | undefined => {
    if (!crepeInstance) return;

    return crepeInstance.editor.action((ctx) => {
      const view = ctx.get(editorViewCtx);
      return view.state.doc;
    });
  };

  /**
   * Finds the top-level range of a section identified by its heading id.
   * The range spans from the heading until the next heading of the same or
   * higher level.
   *
   * @param doc - The ProseMirror document to search.
   * @param sectionId - The unique id of the section's heading node.
   * @returns The position range of the section, or undefined if not found.
   */
  const findSectionRange = (
    doc: PMNode,
    sectionId: string,
  ): { from: number; to: number } | undefined => {
    const blocks: { node: PMNode; pos: number }[] = [];
    doc.forEach((node, offset) => {
      blocks.push({ node, pos: offset });
    });

    const startIndex = blocks.findIndex(
      (block) => block.node.type.name === "heading" && block.node.attrs.id === sectionId,
    );
    if (startIndex === -1) return;

    const level = blocks[startIndex].node.attrs.level as number;
    let to = doc.content.size;
    for (let i = startIndex + 1; i < blocks.length; i++) {
      const block = blocks[i];
      if (
        block.node.type.name === "heading" &&
        (block.node.attrs.level as number) <= level
      ) {
        to = block.pos;
        break;
      }
    }

    return { from: blocks[startIndex].pos, to };
  };

  /**
   * Builds a structured outline of the document by walking its top-level
   * nodes. Each heading starts a new section; subsequent non-heading nodes
   * are attached as content of that section.
   *
   * @returns An array of sections, or undefined if the editor is not ready.
   */
  const getSections = (): Section[] | undefined => {
    const docStructure = getDoc();
    if (!docStructure) return;

    const sections: Section[] = [];
    let currentIndex = -1;

    docStructure.content.content.forEach((node) => {
      if (node.type.name === "heading") {
        sections.push({
          id: node.attrs.id,
          text: node.content.content[0]?.text,
          content: [],
          level: node.attrs.level,
        });
        currentIndex += 1;
      } else if (currentIndex >= 0) {
        const content: Content = {
          text: node.content.content[0]?.text,
          type: node.type.name,
          size: node.content.size,
          parent: sections[currentIndex].id,
        };
        sections[currentIndex].content.push(content);
      }
    });

    return sections;
  };

  // ---------------------------------------------------------------------------
  // Editor lifecycle
  // ---------------------------------------------------------------------------

  /**
   * Creates and initializes the Crepe editor instance.
   * Used via Svelte's `use:` directive so the DOM element is passed in.
   *
   * @param dom - The DOM element to mount the editor to.
   * @param onReady - Optional callback fired when editor is ready.
   * @returns Object with destroy method for cleanup.
   */
  const createEditor = (
    dom: HTMLElement,
    { onReady }: { onReady?: (crepe: Crepe) => void } = {},
  ) => {
    const crepe = new Crepe({
      root: dom,
      defaultValue: DEFAULT_CONTENT,
      featureConfigs: {
        [Crepe.Feature.Placeholder]: {
          text: PLACEHOLDER_TEXT,
          mode: "doc",
        },
      },
    });

    crepe.editor.use(protectSectionPlugin);
    crepe.on((listener) => {
      listener.markdownUpdated((ctx, md, prevMd)=> {
        editorContent.set(md) 
      })

      listener.updated(() => {
        const newTitle = getDocTitle()
        if (newTitle.length === 0) {
          editorTitle.set(null)
        } else {
          editorTitle.set(newTitle)
        }
      })
    })
    crepe.create().then(() => {
      onReady?.(crepe);
      crepe.editor.action((ctx) => {
        ctx.get(editorViewCtx).focus();
      });
    });

    return {
      destroy() {
        crepe.destroy();
      },
    };
  };

  /**
   * Callback fired when the Crepe editor finishes initializing.
   * Stores the instance so later operations can access the editor.
   */
  const handleReady = (crepe: Crepe) => {
    crepeInstance = crepe;
  };

  $effect(() => {
    const md = content 
    const inst = crepeInstance
    if (md && inst) {
      inst.editor.action(replaceAll(md))
      editorContent.set(md)
    }
  })

  // ---------------------------------------------------------------------------
  // Public API (exposed to parent components)
  // ---------------------------------------------------------------------------

  /**
   * Returns the full document outline (all sections with their content).
   * @returns An array of sections, or undefined if the editor is not ready.
   */
  export const getOutline = () => getSections();

  /**
   * Finds a single section by its id.
   * @param id - The unique identifier of the section's heading.
   * @returns The matching section, or undefined if not found / not ready.
   */
  export const getSectionById = (id: string): Section | undefined => {
    return getSections()?.find((section) => section.id === id);
  };

  /**
   * Returns the text of the first heading, used as the default document title.
   * @returns The title text, or an empty string if none exists.
   */
  export const getDocTitle = () => {
    const doc = getDoc();
    const firstHeading = doc?.content.content.find(
      (node) => node.type.name === "heading",
    );
    return firstHeading?.content.content[0]?.text ?? "";
  };

  /**
   * Locks or unlocks a section by its ID by setting the readOnly attribute.
   * @param sectionId - The unique identifier of the section to lock/unlock.
   * @param isLocked - True to lock (make read-only), false to unlock.
   */
  export const setSectionLock = (sectionId: string, isLocked: boolean) => {
    if (!crepeInstance) return;

    crepeInstance.editor.action((ctx) => {
      const view = ctx.get(editorViewCtx);
      const { state, dispatch } = view;

      const range = findSectionRange(state.doc, sectionId);
      if (!range) {
        console.warn(`Section "${sectionId}" not found`);
        return;
      }

      // Apply readOnly to all nodes in the section range
      const tr = state.tr;
      state.doc.nodesBetween(range.from, range.to, (node, pos) => {
        if (
          !node.isText &&
          node.type.spec.attrs?.readOnly &&
          node.attrs.readOnly !== isLocked
        ) {
          tr.setNodeMarkup(pos, undefined, {
            ...node.attrs,
            readOnly: isLocked,
          });
        }
        return true;
      });

      if (tr.docChanged) dispatch(tr);
    });
  };

  /**
   * Replaces the content of a section identified by its id.
   * TODO: Implementation pending — needs to splice new content into the
   * document within the section range.
   *
   * @param id - The unique identifier of the section to update.
   * @param _content - The new markdown content for the section.
   */
  export const setSectionContent = (id: string, _content: string) => {
    void id;
    void _content;
  };
</script>

<!-- Mount point for the Crepe editor -->
<div use:createEditor={{ onReady: handleReady }}></div>

<style>
  /* Style for locked blocks */
  .locked-section {
    background-color: #f3f4f6;
    border-left: 4px solid #ef4444;
    padding: 8px 12px;
    user-select: none; /* Prevents text highlighting */
    cursor: not-allowed;
  }
</style>
