"""Schema definitions for agent-personal-vault."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FieldSpec:
    label: str
    group: str
    sensitivity: str = "personal"
    optional: bool = False
    hint: str = ""
    example: str = ""
    input_type: str = "text"
    options: tuple[str, ...] = ()


JOB_HUNTING_PROFILE: dict[str, FieldSpec] = {
    "FAMILY_NAME": FieldSpec("姓", "identity", hint="正式表記", example="山田"),
    "GIVEN_NAME": FieldSpec("名", "identity", hint="正式表記", example="太郎"),
    "FAMILY_NAME_KANA": FieldSpec("姓ふりがな", "identity", example="やまだ"),
    "GIVEN_NAME_KANA": FieldSpec("名ふりがな", "identity", example="たろう"),
    "BIRTH_DATE": FieldSpec("生年月日", "identity", input_type="date", example="2000-04-01"),
    "POSTAL_CODE": FieldSpec("郵便番号", "contact", example="100-0001"),
    "PREFECTURE": FieldSpec(
        "都道府県",
        "contact",
        example="東京都",
        options=(
            "",
            "北海道",
            "青森県",
            "岩手県",
            "宮城県",
            "秋田県",
            "山形県",
            "福島県",
            "茨城県",
            "栃木県",
            "群馬県",
            "埼玉県",
            "千葉県",
            "東京都",
            "神奈川県",
            "新潟県",
            "富山県",
            "石川県",
            "福井県",
            "山梨県",
            "長野県",
            "岐阜県",
            "静岡県",
            "愛知県",
            "三重県",
            "滋賀県",
            "京都府",
            "大阪府",
            "兵庫県",
            "奈良県",
            "和歌山県",
            "鳥取県",
            "島根県",
            "岡山県",
            "広島県",
            "山口県",
            "徳島県",
            "香川県",
            "愛媛県",
            "高知県",
            "福岡県",
            "佐賀県",
            "長崎県",
            "熊本県",
            "大分県",
            "宮崎県",
            "鹿児島県",
            "沖縄県",
        ),
    ),
    "CITY_ADDRESS": FieldSpec("市区町村", "contact", example="千代田区千代田"),
    "STREET_ADDRESS": FieldSpec("番地", "contact", example="1-1"),
    "BUILDING_NAME": FieldSpec("建物名・部屋番号", "contact", optional=True, example="サンプルマンション101"),
    "ADDRESS": FieldSpec("住所（提出用）", "contact", example="東京都千代田区千代田1-1 サンプルマンション101"),
    "PHONE": FieldSpec("電話番号", "contact", example="090-1234-5678"),
    "EMAIL": FieldSpec("メール", "contact", example="taro@example.test"),
    "GRADUATION_PERIOD": FieldSpec("卒業・修了予定時期", "education", example="2099年12月"),
    "SCHOOL_TYPE": FieldSpec("学校区分", "education", example="大学", options=("", "大学", "大学院", "短期大学", "専門学校", "高等専門学校", "その他")),
    "ACADEMIC_FIELD_TYPE": FieldSpec("文理区分", "education", example="文系", options=("", "文系", "理系", "文理融合", "その他")),
    "UNIVERSITY_NAME": FieldSpec("大学名", "education", example="サンプル大学"),
    "FACULTY_NAME": FieldSpec("学部名", "education", optional=True, example="サンプル学部"),
    "DEPARTMENT_NAME": FieldSpec("学科名", "education", optional=True, example="サンプル学科"),
    "GRADUATE_SCHOOL_NAME": FieldSpec("大学院・研究科名", "graduate", optional=True, example="サンプル研究科"),
    "GRADUATE_MAJOR_NAME": FieldSpec("専攻名", "graduate", optional=True, example="サンプル専攻"),
    "DEGREE": FieldSpec("学位", "graduate", optional=True, example="修士", options=("", "学士", "修士", "博士", "短期大学士", "専門士", "高度専門士", "その他")),
    "ENROLLMENT_DATE": FieldSpec("大学入学年月", "education", input_type="month", example="2022-04"),
    "COMPLETION_DATE": FieldSpec("大学卒業年月", "education", optional=True, example="2026-03 卒業見込み"),
    "GRADUATE_ENROLLMENT_DATE": FieldSpec("大学院入学年月", "graduate", optional=True, input_type="month", example="2026-04"),
    "GRADUATE_COMPLETION_DATE": FieldSpec("大学院修了年月", "graduate", optional=True, example="2028-03 修了見込み"),
    "HIGH_SCHOOL_NAME": FieldSpec("高校名", "extra_education", optional=True, example="サンプル高等学校"),
    "HIGH_SCHOOL_GRADUATION_DATE": FieldSpec("高校卒業年月", "extra_education", optional=True, input_type="month", example="2022-03"),
    "QUALIFICATIONS": FieldSpec("資格", "qualifications", optional=True, example="2024年6月 サンプル資格"),
    "FACE_PHOTO_PATH": FieldSpec("顔写真ファイルパス", "assets", optional=True, example="assets/photo.jpg"),
    "NOTES": FieldSpec("補足", "notes", optional=True, example="応募先ごとに変わる情報は固定しない"),
}


DERIVED_FIELDS: dict[str, str] = {
    "FULL_NAME": "氏名（自動生成）",
    "FULL_NAME_KANA": "ふりがな（自動生成）",
    "NAME_SEPARATOR": "氏名の区切り（固定: 全角スペース）",
}


SCHEMAS: dict[str, dict[str, FieldSpec]] = {
    "job_hunting_profile": JOB_HUNTING_PROFILE,
}
