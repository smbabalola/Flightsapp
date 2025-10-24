# Kubernetes Deployment

This directory contains Kubernetes manifests for deploying SureFlights to a staging environment.

## Quick Start

```bash
# 1. Create namespace
kubectl apply -f namespace.yaml

# 2. Update secrets with your values
# Edit secrets.yaml and base64 encode your secrets
echo -n 'your-secret' | base64

# 3. Apply secrets and configmap
kubectl apply -f secrets.yaml
kubectl apply -f configmap.yaml

# 4. Deploy services
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

# 5. (Optional) Deploy ingress
kubectl apply -f ingress.yaml

# 6. Verify deployment
kubectl get all -n sureflights-staging
```

## Files

- `namespace.yaml` - Creates the staging namespace
- `configmap.yaml` - Non-sensitive configuration
- `secrets.yaml` - Sensitive credentials (base64 encoded)
- `deployment.yaml` - Pod deployments for app, postgres, and redis
- `service.yaml` - Service definitions for networking
- `ingress.yaml` - Ingress for external access (optional)

## Update Deployment

```bash
# Update image
kubectl set image deployment/sureflights-api \
  sureflights-api=ghcr.io/your-org/sureflights:staging-latest \
  -n sureflights-staging

# Watch rollout
kubectl rollout status deployment/sureflights-api -n sureflights-staging
```

## Troubleshooting

```bash
# Check pod status
kubectl get pods -n sureflights-staging

# View logs
kubectl logs -l app=sureflights-api -n sureflights-staging

# Describe pod for events
kubectl describe pod <pod-name> -n sureflights-staging

# Port forward for local access
kubectl port-forward svc/sureflights-api-service 8001:80 -n sureflights-staging
```

## Clean Up

```bash
# Delete all resources
kubectl delete -f .

# Or delete namespace (deletes everything)
kubectl delete namespace sureflights-staging
```

For detailed instructions, see [STAGING_DEPLOYMENT.md](../STAGING_DEPLOYMENT.md).
