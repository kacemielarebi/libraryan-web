from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import CompanyInfo
from .serializers import CompanyInfoSerializer
from .permissions import IsAdminAccount
# --------------------------------------------------
# 📌 جلب معلومات المؤسسة (الصف الأول فقط)
# --------------------------------------------------
@api_view(['GET'])
def get_company_info(request):
    try:
        company = CompanyInfo.objects.first()
        if not company:
            # إرجاع كائن فارغ بدلاً من خطأ
            return Response({
                "name": "",
                "description": "",
                "email": "",
                "phone": "",
                "privacy_policy": ""
            })
        serializer = CompanyInfoSerializer(company)
        return Response(serializer.data)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

# --------------------------------------------------
# ✏️ تعديل معلومات المؤسسة (الصف الأول فقط)
# --------------------------------------------------
@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated,IsAdminAccount])  # فقط مستخدم مسجل يقدر يعدل
def update_company_info(request):
    # محاولة الحصول على أول سجل لمعلومات المؤسسة
    company = CompanyInfo.objects.first()
    
    if not company:
        # إذا لم توجد معلومات، نقوم بإنشاء سجل جديد بالبيانات المرسلة
        serializer = CompanyInfoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # إذا وجدت المعلومات، نقوم بتحديثها جزئيًا
    serializer = CompanyInfoSerializer(company, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)