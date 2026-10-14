package com.diet.config;

import io.agentscope.core.model.Model;
import io.agentscope.core.model.OpenAIChatModel;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * AgentScope 模型配置。
 *
 * <p>统一走 OpenAI 兼容协议，因此既可以指向阿里云百炼 DashScope 的兼容模式，
 * 也可以指向本地/自建的 OpenAI 兼容网关（例如 http://127.0.0.1:7863/v1）。
 *
 * <p>相关配置项：
 * <pre>
 * diet.llm.base-url     网关地址，例如 http://127.0.0.1:7863/v1
 * diet.llm.api-key      网关 API Key
 * diet.llm.main-model   主模型（推荐理由、最终应答）
 * diet.llm.light-model  轻量模型（意图识别、澄清追问）
 * </pre>
 */
@Configuration
public class DietAgentScopeConfig {

    /** OpenAI 兼容网关的 base-url（含 /v1）。 */
    @Value("${diet.llm.base-url:}")
    private String baseUrl;

    /** 网关 API Key。 */
    @Value("${diet.llm.api-key:}")
    private String apiKey;

    /** 主模型，用于推荐理由和最终应答。 */
    @Value("${diet.llm.main-model:qwen-max}")
    private String mainModelName;

    /** 轻量模型，用于意图识别和澄清追问。 */
    @Value("${diet.llm.light-model:qwen-turbo}")
    private String lightModelName;

    /**
     * 主模型 Bean。RecommendResponseAgent / PlanResponseAgent 会优先使用该模型。
     * 保留原 Bean 名 "DietMainChatModel"，避免改动注入点。
     */
    @Bean("DietMainChatModel")
    public Model DietMainChatModel() {
        return buildModel(mainModelName);
    }

    /**
     * 轻量模型 Bean。IntentAgent 和 ClarifyAgent 使用它降低延迟与成本。
     * 保留原 Bean 名 "DietLightChatModel"。
     */
    @Bean("DietLightChatModel")
    public Model DietLightChatModel() {
        return buildModel(lightModelName);
    }

    /** 构造一个指向 OpenAI 兼容网关的 ChatModel。 */
    private Model buildModel(String modelName) {
        return OpenAIChatModel.builder()
                .apiKey(apiKey)
                .baseUrl(baseUrl)
                .modelName(modelName)
                .build();
    }
}
