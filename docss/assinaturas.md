Prompt
Desenvolva um modelo mínimo de assinaturas para implementação no backend, com a seguinte estrutura e requisitos:

1. Modelo de Dados Principal:
   - Entidade `Assinatura` com campos:
     * ID único
     * Tipo (organização/tenant ou adepto)
     * Plano associado (free, freemium, premium)
     * Data de início/término
     * Status (ativa, cancelada, expirada)
     * Método de pagamento
     * Valor e periodicidade (mensal, anual)

2. Modelos Específicos:
   - Para Organizações/Tenants:
     * Plano free com limitações claras (ex: número de adeptos, recursos disponíveis)
     * Campos para cálculo de ganhos futuros (comissão por assinatura)
   
   - Para Adeptos:
     * Planos freemium com benefícios básicos
     * Relacionamento com organizações seguidas
     * Campos de preferências e notificações

3. Componentes Frontend Base:
   - Utilize como referência os componentes existentes:
     * `c:\Project\bolayetu\frontend\pages\public\Features.tsx` (Features) - para exibir benefícios dos planos
     * `c:\Project\bolayetu\frontend\pages\public\Pricing.tsx` (Pricing) - para tabelas comparativas de preços
     * `c:\Project\bolayetu\frontend\pages\Subscription.tsx` (Subscription) - para gestão de assinaturas

4. Requisitos Técnicos:
   - API RESTful com endpoints para:
     * CRUD de assinaturas
     * Gestão de planos
     * Cálculo de ganhos para organizadores
   - Autenticação e autorização por tipo de usuário
   - Integração com gateway de pagamentos
   - Sistema de notificações para eventos de assinatura

5. Validações:
   - Impedir conflitos entre planos
   - Garantir consistência nos períodos de assinatura
   - Validar limites de uso conforme tipo de plano

6. Documentação:
   - Esquema do banco de dados
   - Diagrama de relações entre entidades
   - Especificação dos endpoints da API

7. Próximos Passos:
   - Mapear fluxos completos de:
     * Assinatura inicial
     * Upgrade/downgrade de plano
     * Cancelamento
     * Renovação automática
   - Definir métricas de acompanhamento (ex: número de adeptos assinantes)



Segue um modelo mínimo de assinaturas desenhado para o backend, pronto para evoluir com billing real, ganhos de organizadores e planos freemium/free.

Vou focar em: modelo de dados, como ele cobre os cenários (tenant e adepto), validações chave e como ele se encaixa com os componentes de frontend que já existem.

---

**1. Modelo de dados principal (Plano + Assinatura)**

Arquivo: [backend/assinaturas/models.py](file:///c:/Project/bolayetu/backend/assinaturas/models.py)

**a) SubscriptionPlan** – catálogo de planos

Pensado para ser genérico e cobrir tanto planos de organização (tenant) quanto planos de adeptos.

```python
class SubscriptionPlan(BaseModel):
    TARGET_CHOICES = (
        ("tenant", "Tenant"),
        ("fan", "Fan"),
    )

    PLAN_TYPE_CHOICES = (
        ("free", "Free"),
        ("freemium", "Freemium"),
        ("premium", "Premium"),
    )

    BILLING_PERIOD_CHOICES = (
        ("monthly", "Monthly"),
        ("yearly", "Yearly"),
    )

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    target_type = models.CharField(max_length=20, choices=TARGET_CHOICES)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES)
    price_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default="AOA")
    billing_period = models.CharField(max_length=20, choices=BILLING_PERIOD_CHOICES, default="monthly")
    is_active = models.BooleanField(default=True)

    max_active_tournaments = models.PositiveIntegerField(null=True, blank=True)
    max_clubs = models.PositiveIntegerField(null=True, blank=True)
    max_followers = models.PositiveIntegerField(null=True, blank=True)

    organizer_commission_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
```

- **Cobertura dos requisitos:**
  - Tipo de plano: `plan_type` = free/freemium/premium.
  - Plano para **organização** vs **adepto**: `target_type` = "tenant" ou "fan".
  - Preço e periodicidade: `price_amount`, `currency`, `billing_period`.
  - Limitações claras:
    - `max_active_tournaments`, `max_clubs` para tenants (ex.: plano free com 1 torneio e 8 equipas).
    - `max_followers` pode ser usado para limitar número de adeptos num plano de organização.
  - Campos para cálculo de ganhos futuros:
    - `organizer_commission_percent` define a percentagem da receita de cada assinatura que deve ir para o organizador (tenant).

Isso casa bem com o que já aparece em [Pricing.tsx](file:///c:/Project/bolayetu/frontend/pages/public/Pricing.tsx#L9-L59) (Starter / Pro / Elite) – estes passam a ser registros de `SubscriptionPlan` com `code` `"starter"`, `"pro"`, `"elite"` e diferentes `price_amount`, `plan_type` e `target_type="tenant"`.

---

**b) Subscription (Assinatura)** – instância de assinatura concreta

Suporta dois tipos:

- Assinatura de **plano de organização** (para tenants).
- Assinatura de **adepto** para seguir uma organização com um plano freemium/premium.

```python
class Subscription(BaseModel):
    SUBSCRIBER_TYPE_CHOICES = (
        ("tenant", "Tenant"),
        ("fan", "Fan"),
    )

    STATUS_CHOICES = (
        ("active", "Active"),
        ("canceled", "Canceled"),
        ("expired", "Expired"),
        ("pending", "Pending"),
    )

    PAYMENT_METHOD_CHOICES = (
        ("none", "None"),
        ("offline", "Offline"),
        ("gateway", "Gateway"),
    )

    subscriber_type = models.CharField(max_length=20, choices=SUBSCRIBER_TYPE_CHOICES)

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="plan_subscriptions", null=True, blank=True)
    fan = models.ForeignKey(User, on_delete=models.CASCADE, related_name="plan_subscriptions", null=True, blank=True)
    organization = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="fan_plan_subscriptions", null=True, blank=True)

    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name="subscriptions")

    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default="none")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    billing_period = models.CharField(max_length=20, choices=SubscriptionPlan.BILLING_PERIOD_CHOICES, default="monthly")
    external_payment_id = models.CharField(max_length=100, blank=True, default="")

    organizer_share = models.DecimalField(max_digits=10, decimal_places=2, default=0)
```

- **Interpretação dos campos por tipo:**

  - `subscriber_type = "tenant"`:
    - `tenant` obrigatório (organização que compra o plano da plataforma).
    - `plan.target_type` será `"tenant"`.
    - `organization` e `fan` vazios.
    - Representa **Assinatura de Planos para as organizações/tenant**.

  - `subscriber_type = "fan"`:
    - `fan` obrigatório (User).
    - `organization` obrigatório (Tenant seguido).
    - `plan.target_type` será `"fan"`.
    - `tenant` vazio.
    - Representa **assinaturas para adeptos seguirem as suas organizações**, inclusive quando forem planos freemium/premium.

- **Pagamento e periodicidade:**
  - `payment_method`: mínimo para integração futura com gateway (`none`, `offline`, `gateway`).
  - `amount`: valor final cobrado (pode ser igual a `plan.price_amount` ou ajustado por promoções).
  - `billing_period`: duplicado aqui para garantir consistência da assinatura ao longo da sua vida.
  - `external_payment_id`: referência ao gateway (Multicaixa / outro).

---

**2. Validações essenciais**

Ainda em [assinaturas/models.py](file:///c:/Project/bolayetu/backend/assinaturas/models.py#L63-L119), o método `clean` garante consistência:

```python
def clean(self):
    from django.core.exceptions import ValidationError

    if self.subscriber_type == "tenant":
        if not self.tenant:
            raise ValidationError({"tenant": "Tenant é obrigatório para assinaturas de organização."})
        if self.fan or self.organization:
            raise ValidationError({"subscriber_type": "Assinaturas de organização não podem ter fan ou organização associados."})

    if self.subscriber_type == "fan":
        if not self.fan or not self.organization:
            raise ValidationError({"subscriber_type": "Assinaturas de adepto requerem fan e organização."})
        if self.tenant:
            raise ValidationError({"tenant": "Não associe tenant diretamente em assinaturas de adepto."})

    if self.billing_period != self.plan.billing_period:
        raise ValidationError({"billing_period": "Período de faturação deve coincidir com o plano."})

    if self.end_date and self.end_date < self.start_date:
        raise ValidationError({"end_date": "Data de término não pode ser anterior à data de início."})

    if self.status == "active":
        qs = Subscription.objects.filter(
            subscriber_type=self.subscriber_type,
            plan__target_type=self.plan.target_type,
            status="active",
        )
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        if self.subscriber_type == "tenant" and self.tenant:
            qs = qs.filter(tenant=self.tenant)
        if self.subscriber_type == "fan" and self.fan and self.organization:
            qs = qs.filter(fan=self.fan, organization=self.organization)
        if qs.exists():
            raise ValidationError({"status": "Já existe uma assinatura ativa para este contexto."})
```

- **Conflitos entre planos:**
  - Só permite **uma assinatura ativa por contexto**:
    - Para tenant: um plano ativo por tenant/target_type.
    - Para fan: um plano ativo por par (fan, organization)/target_type.

- **Consistência dos períodos:**
  - `billing_period` da assinatura deve ser igual ao do plano (`plan.billing_period`).
  - `end_date >= start_date`.

- **Limites por plano:**
  - Guardados no `SubscriptionPlan` (`max_active_tournaments`, etc.).
  - Podem ser validados em serviços que criam/atualizam recursos (ex.: ao criar torneio, check se tenant ultrapassou `max_active_tournaments` do plano ativo).

---

**3. Cálculo de ganhos para organizadores**

Ainda em `Subscription`:

```python
def save(self, *args, **kwargs):
    if not self.amount:
        self.amount = self.plan.price_amount
    if not self.organizer_share and self.plan.organizer_commission_percent:
        self.organizer_share = (self.amount * self.plan.organizer_commission_percent) / 100
    super().save(*args, **kwargs)

@classmethod
def total_organizer_earnings(cls, tenant):
    return (
        cls.objects.filter(organization=tenant, status="active").aggregate(total=Sum("organizer_share")).get("total")
        or 0
    )
```

- **Para assinaturas de adeptos:**
  - `organization` é o tenant seguido.
  - `organizer_commission_percent` define a percentagem para o organizador.
  - `organizer_share` é calculado automaticamente com base em `amount`.
  - `total_organizer_earnings(tenant)` devolve o somatório de ganhos daquele organizador em todas as assinaturas ativas de adeptos.

- **Para planos de tenant:**
  - Poderá ser usado para cashback, parcerias, etc., ajustando a forma como `organizer_share` é calculado no futuro.

---

**4. Notificações de eventos de assinatura**

Integração mínima com o app `notifications`, sem acoplar a um gateway:

```python
@receiver(post_save, sender=Subscription)
def subscription_post_save(sender, instance, created, **kwargs):
    try:
        user = None
        title = ""
        message = ""
        if instance.subscriber_type == "tenant" and instance.tenant:
            user = User.objects.filter(tenant=instance.tenant, role__in=["admin", "manager"]).first()
            title = "Plano de organização atualizado"
            if created:
                message = f"Novo plano {instance.plan.name} ativado para a organização {instance.tenant.name}."
            else:
                message = f"Assinatura da organização {instance.tenant.name} foi atualizada para o plano {instance.plan.name}."
        if instance.subscriber_type == "fan" and instance.fan and instance.organization:
            user = instance.fan
            title = "Assinatura de adepto atualizada"
            if created:
                message = f"Está agora a seguir {instance.organization.name} com o plano {instance.plan.name}."
            else:
                message = f"A sua assinatura para {instance.organization.name} foi atualizada para o plano {instance.plan.name}."
        if user and title and message:
            Notification.objects.create(
                user=user,
                title=title,
                message=message,
                type="info",
            )
    except Exception:
        if settings.DEBUG:
            raise
```

- Cobre o requisito de **sistema de notificações para eventos de assinatura**:
  - Administradores/gestores da organização são notificados quando o plano do tenant muda.
  - Adeptos são notificados quando criam/alteram a sua assinatura para uma organização.

---

**5. Como isso conversa com o frontend atual**

- **Features.tsx** e **Pricing.tsx**:
  - Já apresentam as diferenças de planos (Starter/Pro/Elite, benefícios, preços).
  - Esses planos devem ser representados como `SubscriptionPlan` do tipo `target_type="tenant"`, com os limites coerentes:
    - Starter → `plan_type="free"`, `price_amount=0`, `max_active_tournaments=1`, `max_clubs=8`.
    - Pro → `plan_type="premium"`, `price_amount=15000`, limites maiores.
    - Elite → `plan_type="premium"`, `price_amount=45000`, limites praticamente sem restrição.

- **Subscription.tsx**:
  - Pode consumir endpoints futuros:
    - `GET /api/subscriptions/me/tenant/` → ver a assinatura atual da organização do utilizador.
    - `GET /api/subscriptions/me/fan/` → ver as assinaturas de adepto.
    - `GET /api/subscription-plans/?target_type=tenant` → listar planos da tabela de Pricing.

- **User.hasActiveSubscription** (frontend) e regras de acesso:
  - O backend passa a ter uma estrutura clara para, no futuro, expor:
    - `has_active_subscription` para tenant (plano da organização).
    - `fan_has_premium` ou similar para adeptos.
  - Esses flags podem ser derivados da tabela `Subscription` e expostos em `/api/auth/me/` para alimentar o `AuthContext` e o `ProtectedRoute` com `requireSubscription`.

---

**6. API RESTful (esboço para próximos passos)**

Não implementei os endpoints ainda, mas o modelo já está preparado para:

- Recursos:
  - `/api/subscription-plans/` – CRUD de planos (apenas admin).
  - `/api/subscriptions/` – CRUD de assinaturas:
    - POST para criar assinatura de tenant (plano de organização).
    - POST para criar assinatura de fan→organization.
  - Endpoints auxiliares:
    - `/api/subscriptions/organizers/{tenant_id}/earnings/` – cálculo de ganhos para organizador com base em `organizer_share`.

- Autorização:
  - Admin cria/edita planos (`SubscriptionPlanViewSet` com `IsAdmin`).
  - Managers/admins de tenant gerem a assinatura da sua organização.
  - Adeptos gerem as suas próprias assinaturas para organizações.

---

**7. Gateway de pagamentos e fluxos futuros**

Com a estrutura atual, os fluxos que pediu podem ser mapeados assim:

- **Assinatura inicial**
  - Criar `Subscription` com `status="pending"`, `payment_method="gateway"`.
  - Após callback do gateway, atualizar `status` para `"active"`, `start_date`, `end_date`, e preencher `external_payment_id`.

- **Upgrade/downgrade de plano**
  - Criar nova `Subscription` ativa e marcar a anterior como `"canceled"` ou `"expired"` (respeitando validação que impede duas ativas para o mesmo contexto).

- **Cancelamento**
  - Atualizar `status` para `"canceled"` e, opcionalmente, ajustar `end_date`.

- **Renovação automática**
  - Job periódico que:
    - Verifica `end_date` e `billing_period`.
    - Cria nova assinatura com novo período e tenta cobrança via gateway.

- **Métricas de acompanhamento**
  - Número de assinaturas ativas por plano (`SubscriptionPlan.subscriptions.filter(status="active").count()`).
  - Receita total por plano, por tenant, por período.
  - Ganhos acumulados por organizador (`total_organizer_earnings`).

---

Se quiser, no próximo passo posso:

- Criar os serializers + viewsets básicos para `SubscriptionPlan` e `Subscription` no app `assinaturas`, com permissões por tipo de utilizador.
- Desenhar explicitamente os endpoints REST (métodos, payloads e respostas) para que o frontend (Pricing/Subscription) possa consumir diretamente.




          
Avancei a iteração implementando a camada mínima de API para o sistema de assinaturas, alinhada com o modelo que definimos.

Vou resumir o que já está disponível e como usar.

---

**1. Serializers de planos e assinaturas**

Arquivo: [backend/assinaturas/serializers.py](file:///c:/Project/bolayetu/backend/assinaturas/serializers.py)

- **SubscriptionPlanSerializer**
  - Campos expostos:
    - Identidade e descrição: `id`, `code`, `name`, `description`
    - Alvo e tipo: `target_type` (`tenant` ou `fan`), `plan_type` (`free`, `freemium`, `premium`)
    - Preço: `price_amount`, `currency`
    - Ciclo: `billing_period` (`monthly`, `yearly`)
    - Estado: `is_active`
    - Limites: `max_active_tournaments`, `max_clubs`, `max_followers`
    - Comissão: `organizer_commission_percent`
    - Metadados: `created_at`, `updated_at`

- **SubscriptionSerializer**
  - Exposição:
    - `plan` como objeto completo (read-only, usando SubscriptionPlanSerializer).
    - `plan_id` como campo write-only para setar o plano ao criar/atualizar.
  - Campos principais:
    - Identidade do assinante: `subscriber_type`, `tenant`, `fan`, `organization`
    - Plano: `plan`, `plan_id`
    - Período e status: `start_date`, `end_date`, `status`
    - Pagamento: `payment_method`, `amount`, `billing_period`, `external_payment_id`
    - Ganho do organizador: `organizer_share` (read-only)
    - Metadados: `created_at`, `updated_at`

Isto deixa a API pronta para alimentar telas tipo Pricing/Subscription com objetos já estruturados.

---

**2. Viewsets e permissões**

Arquivo: [backend/assinaturas/views.py](file:///c:/Project/bolayetu/backend/assinaturas/views.py)

- **SubscriptionPlanViewSet**
  - Rota base: `/api/subscriptions/plans/`
  - Permissões:
    - `list` e `retrieve`: `AllowAny` (para que páginas públicas como Pricing e Features possam listar planos).
    - `create`, `update`, `partial_update`, `destroy`: `IsAdmin` (apenas utilizadores com role `admin` no nosso sistema).
  - Endpoints:
    - `GET /api/subscriptions/plans/` – lista planos.
    - `GET /api/subscriptions/plans/{id}/` – detalhe de um plano.
    - `POST/PUT/PATCH/DELETE` – gestão de planos (admin).

- **SubscriptionViewSet**
  - Rota base: `/api/subscriptions/`
  - Permissões:
    - `permission_classes = [IsAuthenticated]` – só utilizadores autenticados mexem em assinaturas.
  - Queryset filtrado por contexto do utilizador:
    ```python
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or getattr(user, "role", "") == "admin":
            return Subscription.objects.all()
        tenant = getattr(user, "tenant", None)
        qs = Subscription.objects.none()
        if tenant:
            qs = qs | Subscription.objects.filter(subscriber_type="tenant", tenant=tenant)
            qs = qs | Subscription.objects.filter(subscriber_type="fan", organization=tenant)
        qs = qs | Subscription.objects.filter(subscriber_type="fan", fan=user)
        return qs
    ```
    - Admin:
      - Vê todas as assinaturas (útil para backoffice).
    - Manager/Admin de tenant:
      - Vê:
        - Assinaturas de plano do próprio tenant (`subscriber_type="tenant", tenant=tenant`).
        - Assinaturas de adeptos para a sua organização (`subscriber_type="fan", organization=tenant`).
    - Adepto:
      - Vê apenas as suas assinaturas (`subscriber_type="fan", fan=user`).

  - Criação com preenchimento automático do contexto:
    ```python
    def perform_create(self, serializer):
        user = self.request.user
        subscriber_type = serializer.validated_data.get("subscriber_type")
        if subscriber_type == "tenant":
            tenant = getattr(user, "tenant", None)
            serializer.save(tenant=tenant)
        elif subscriber_type == "fan":
            serializer.save(fan=user)
        else:
            serializer.save()
    ```
    - Para assinaturas de organização: o tenant vem do utilizador autenticado.
    - Para assinaturas de adepto: o fan é sempre o utilizador autenticado.

---

**3. Ações auxiliares na API**

Ainda em [assinaturas/views.py](file:///c:/Project/bolayetu/backend/assinaturas/views.py#L28-L62):

- **Assinatura atual do tenant (organização)**  
  `GET /api/subscriptions/me/tenant/`
  - Retorna a assinatura de plano da organização ligada ao utilizador atual (se houver).
  - Respostas:
    - 400 se o utilizador não tiver `tenant`.
    - 404 se não existir nenhuma assinatura para o tenant.
    - 200 + objeto da assinatura em caso de sucesso.

- **Assinaturas do adepto**  
  `GET /api/subscriptions/me/fan/`
  - Lista todas as assinaturas do tipo fan (`subscriber_type="fan"`) para o utilizador atual.
  - Ideal para alimentar a página [Subscription.tsx] com as organizações/plans que o adepto segue.

---

**4. URLs e integração no projeto**

- Arquivo de URLs do app assinaturas: [backend/assinaturas/urls.py](file:///c:/Project/bolayetu/backend/assinaturas/urls.py)
  ```python
  router = DefaultRouter()
  router.register(r"plans", SubscriptionPlanViewSet, basename="subscription-plan")
  router.register(r"", SubscriptionViewSet, basename="subscription")

  urlpatterns = [
      path("", include(router.urls)),
  ]
  ```

- Inclusão no router global: [backend/config/urls.py](file:///c:/Project/bolayetu/backend/config/urls.py#L7-L26)
  ```python
  path('api/subscriptions/', include('assinaturas.urls')),
  ```

- Resultado:
  - `GET /api/subscriptions/plans/`
  - `GET /api/subscriptions/`
  - `GET /api/subscriptions/me/tenant/`
  - `GET /api/subscriptions/me/fan/`
  - E os outros métodos REST padrão.

---

**5. Admin para gestão rápida**

Arquivo: [backend/assinaturas/admin.py](file:///c:/Project/bolayetu/backend/assinaturas/admin.py)

- `SubscriptionPlanAdmin`
  - Lista: código, nome, target_type, plan_type, preço, billing_period, ativo.
  - Filtros por tipo e ciclo.
- `SubscriptionAdmin`
  - Lista: tipo de assinante, tenant, fan, organização, plano, status, método de pagamento, valor, billing_period.
  - Filtros por tipo, status, método, período.

Isto ajuda a testar e gerir manualmente planos/assinaturas num primeiro momento, antes de integrar tudo com o frontend e o gateway.

---

**6. Estado da implementação e próximos passos naturais**

O que já está pronto:

- Modelo de dados (Plan + Subscription) com:
  - Tipo (tenant/fan), plano free/freemium/premium, data início/fim, status, método de pagamento, valor, periodicidade, comissão.
- Validações de consistência e conflitos mínimos.
- API básica:
  - Planos: listagem pública, gestão por admin.
  - Assinaturas: CRUD autenticado com scoping por utilizador/tenant.
  - Endpoints “me” para tenant e fan.
- Integração com notificações nas mudanças de assinatura (já feita no modelo).

Próxima iteração lógica (se quiser que eu continue):

- Ligar Subscription.tsx e Pricing.tsx à nova API:
  - Pricing ler planos de `/api/subscriptions/plans/?target_type=tenant`.
  - Subscription gerir plano atual da organização (`/api/subscriptions/me/tenant/`, POST/PATCH `/api/subscriptions/`).
- Começar a esboçar integração com gateway (payload mínimo + callback).
- Expor flags como `hasActiveSubscription` no endpoint `/api/auth/me/` usando a tabela de Subscription.

Se quiser, posso avançar diretamente para a integração no frontend (consumo dos endpoints nas páginas de Pricing/Subscription e atualização da `AuthContext` com o estado de assinatura).




Se quiser, posso agora focar especificamente em:

- Ajustar o intervalo de polling (por exemplo, 5s em vez de 10s).
- Integrar WebSocket no TournamentDetails, semelhante ao FanPortal, caso tenha (ou venha a ter) um endpoint WS disponível.