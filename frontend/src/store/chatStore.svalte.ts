import { writable } from "svelte/store";


export type Reference = {
    id: number, 
    title: string,
    description: string 
}
export const chatResponse = writable<string>("")
export const chatReferences = writable<Reference[]>([])
export const responseAvailable = writable(false)
export const miniChatResponses = writable<string[]>([])