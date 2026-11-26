import { CairnMdService } from '#services/cairn_md_service'
import { updateCairnMdSchema } from '#validators/cairn_md'
import { inject } from '@adonisjs/core'
import type { HttpContext } from '@adonisjs/core/http'

@inject()
export default class CairnMdController {
  constructor(private cairnMdService: CairnMdService) {}

  async show({ response }: HttpContext) {
    const content = await this.cairnMdService.read()
    return response.status(200).json({ content })
  }

  async update({ request, response }: HttpContext) {
    const { content } = await request.validateUsing(updateCairnMdSchema)
    // Empty request strings arrive as undefined (AdonisJS null-coerces them);
    // treat that as an explicit "clear the file".
    await this.cairnMdService.write(content ?? '')
    return response.status(200).json({ success: true, message: 'Cairn.md saved successfully' })
  }
}
