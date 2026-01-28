<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Str;

class AnaliseController extends Controller
{
    public function analisar(Request $request)
    {
        $request->validate([
            'texto' => 'required|string'
        ]);

        try {
            $response = Http::timeout(10)->post(
                'http://vigia-ml:8000/analisar',
                ['texto' => $request->texto]
            );

            if (!$response->successful()) {
                throw new \Exception('Serviço ML indisponível');
            }

            $ml = $response->json();

            //Validação defensiva do contrato
            if (!isset($ml['contem_dados_pessoais'])) {
                throw new \Exception('Contrato inválido do serviço ML');
            }

            //Regra institucional (LGPD-safe)
            $acao = (
                ($ml['contem_dados_sensiveis'] ?? false) === true
                || ($ml['confianca'] ?? 0) >= 0.60
            )
            ? 'Revisão antes da publicação'
            : 'Publicação automática';

            return response()->json([
                'trace_id'               => $ml['trace_id'] ?? null,
                'contem_dados_pessoais'  => $ml['contem_dados_pessoais'],
                'contem_dados_sensiveis' => $ml['contem_dados_sensiveis'] ?? false,
                'origem_decisao'         => $ml['origem_decisao'] ?? [],
                'tipos_detectados'       => $ml['tipos_detectados'] ?? [],
                'categorias_sensiveis'   => $ml['categorias_sensiveis'] ?? [],
                'confianca'              => $ml['confianca'] ?? 0,
                //(AUDITORIA / EXPLICABILIDADE)
                'evidencias'             => $ml['evidencias'] ?? [],
                'acao_sugerida'          => $acao
            ]);

        } catch (\Throwable $e) {

            //Fallback seguro (LGPD – princípio da prevenção)
            return response()->json([
                'trace_id'      => \Str::uuid(),
                'status'        => 'erro',
                'mensagem'      => 'Não foi possível analisar o texto. Revisão manual obrigatória.',
                'acao_sugerida' => 'Revisão antes da publicação'
            ], 200);
        }
    }

}
