# Vinculos das ações da interface passando as tarefas dinâmicas (CORRIGIDO)
    botao_normal.click(
        fn=lambda a, i, m, f: processar_geral(a, i, m, f, tarefa="transcrever"),
        inputs=[input_audio, input_idioma, input_modelo, input_formato],
        outputs=[output_status, output_arquivo]
    )

    botao_traducao_en.click(
        fn=lambda a, i, m, f: processar_geral(a, i, m, f, tarefa="traduzir_en"),
        inputs=[input_audio, input_idioma, input_modelo, input_formato],
        outputs=[output_status, output_arquivo]
    )

    botao_traducao_pt.click(
        fn=lambda a, i, m, f: processar_geral(a, i, m, f, tarefa="traduzir_pt"),
        inputs=[input_audio, input_idioma, input_modelo, input_formato],
        outputs=[output_status, output_arquivo]
    )

if __name__ == "__main__":
    app.launch(share=True, debug=True)