export type Component = any
// The `pageContext` that are available in both on the server-side and browser-side
export type PageContext = {
  documentProps?: {
    title: string 
  }
}
