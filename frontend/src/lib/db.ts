import {Dexie, type EntityTable} from "dexie"

interface Document {
    id: number,
    title: string,
    description: string, 
    content: string,
    categoryId: number 
    createdBy: number, 
    createdByName: string,
    createdDateTime: Date, 
    updatedDateTime: Date
}

const db = new Dexie("WaveDatabase") as Dexie & {
documents: EntityTable<Document, "id">
}

db.version(1).stores({
  documents: "id, title, description, content, categoryId, createdBy, createdByName, createdDateTime, updatedDateTime"
})

export type { Document }
export { db }