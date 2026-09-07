import vine from '@vinejs/vine'

// Allow an empty/absent value so the user can clear their Cairn.md — AdonisJS
// converts empty request strings to null, so `optional()` (coerced to '' in the
// controller) is what lets a "clear" through. The cap keeps a single system
// prompt from growing unbounded.
export const updateCairnMdSchema = vine.compile(
  vine.object({
    content: vine.string().maxLength(100_000).optional(),
  })
)
