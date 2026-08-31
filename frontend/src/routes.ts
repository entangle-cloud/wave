import Home from "./routes/Home.svelte";
import NotFound from "./routes/NotFound.svelte";
import Editor from "./routes/Editor.svelte";
import Categories from "./routes/Categories.svelte";
import CategoryView from "./routes/CategoryView.svelte";
import Signup from "./routes/Signup.svelte";
import Login from "./routes/Login.svelte";
import Settings from "./routes/Settings.svelte";
import { wrap } from "svelte-spa-router/wrap";
import { requireAuth, skipIfAuthed } from "./guard";

export default {
  "/": wrap({ component: Home, conditions: [requireAuth] }),
  "/docs": wrap({ component: Editor, conditions: [requireAuth] }),
  "/docs/:id": wrap({ component: Editor, conditions: [requireAuth] }),
  "/categories": wrap({ component: Categories, conditions: [requireAuth] }),
  "/categories/:id": wrap({
    component: CategoryView,
    conditions: [requireAuth],
  }),
  "/settings": wrap({ component: Settings, conditions: [requireAuth] }),
  "/login": wrap({ component: Login, conditions: [skipIfAuthed] }),
  "/signup": wrap({ component: Signup, conditions: [skipIfAuthed] }),
  "*": NotFound,
};
