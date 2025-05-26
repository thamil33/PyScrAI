## PyScrAI Agno-to-Custom Framework Transition Plan


### Phase 1.3 - Scenario Execution (Next Steps)

3. __Scenario Runner Implementation__

   - Create `pyscrai/engines/scenario_runner.py` that uses AgentRuntime + orchestration
   - Implement event processing pipeline connecting scenarios → agents → engines
   - Add result aggregation and state persistence


### Phase 2 - LLM Provider Framework (Medium Priority)

5. __Multi-Provider Support__

   - Extend `llm_factory.py` to support OpenAI, Anthropic, local Ollama
   - Add provider abstraction layer with unified interface
   - Implement rate limiting and retry logic

6. __Enhanced Agent Intelligence__

   - Implement prompt engineering templates in engines
   - Add chain-of-thought reasoning capabilities
   - Connect tool integration system to external APIs

### Phase 3 - Research Platform (Lower Priority)

7. __Analytics & Metrics__

   - Implement comprehensive logging and metrics collection
   - Add data export capabilities for external analysis
   - Create visualization components for real-time monitoring

8. __Experimentation Framework__

   - Build A/B testing capabilities for different agent configurations
   - Add parameter sweep automation
   - Implement reproducible scenario execution with seeds

### Key Architecture Decisions

__Immediate Focus Areas:__

- __Database Layer__: ✅ Complete and working
- __Orchestration__: ✅ Basic structure in place, needs integration
- __Agent-Engine Bridge__: 🔄 In progress, needs completion
- __LLM Integration__: ❌ Needs implementation

__Critical Path:__

1. Fix config/dependency issues → 2. Complete BaseEngine.run() → 3. Connect AgentRuntime to orchestration → 4. Implement LLM calls → 5. Build Scenario Runner

__Success Metrics for Phase 1 Completion:__

- [ ] Execute a complete scenario from template to results
- [ ] Multiple agents interacting within a scenario using real LLM responses
- [ ] Comprehensive logging and state tracking
- [ ] All tests passing without import errors

This plan prioritizes getting a working end-to-end system before adding advanced features, following the research-first principle while maintaining the modular architecture you've established.
