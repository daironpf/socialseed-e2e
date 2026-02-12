package com.socialseed.e2e.actions

import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.project.Project
import com.intellij.openapi.ui.Messages
import java.io.BufferedReader
import java.io.InputStreamReader

class RunAllTestsAction : AnAction() {
    override fun actionPerformed(e: AnActionEvent) {
        val project: Project? = e.project
        if (project == null) return

        try {
            val processBuilder = ProcessBuilder("e2e", "run")
            processBuilder.directory(java.io.File(project.basePath!!))
            val process = processBuilder.start()

            val reader = BufferedReader(InputStreamReader(process.inputStream))
            var line: String?
            val output = StringBuilder()
            while (reader.readLine().also { line = it } != null) {
                output.append(line).append("\n")
            }

            Messages.showInfoMessage(project, "E2E Run Output:\n$output", "SocialSeed E2E")
        } catch (ex: Exception) {
            Messages.showErrorDialog(project, "Error running e2e: ${ex.message}", "SocialSeed E2E Error")
        }
    }
}
