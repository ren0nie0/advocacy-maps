import { requireAuth } from "../components/auth"
import { createPage } from "../components/page"
import {
  usePublishService,
  useSyncRouterAndStore
} from "../components/publish/hooks"
import { SubmitTestimonyForm } from "../components/publish/SubmitTestimonyForm"
import { createGetStaticTranslationProps } from "components/translations"

export default createPage({
  title: "Submit Testimony",
  Page: requireAuth(() => {
    useSyncRouterAndStore()

    return (
      <>
        <usePublishService.Provider />
        <SubmitTestimonyForm />
      </>
    )
  })
})

export const getStaticProps = createGetStaticTranslationProps([
  "common",
  "footer"
])
