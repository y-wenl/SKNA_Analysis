from datetime import datetime
import numpy as np
import json
import re


def ymd_to_date(ymd_str):
    ymd_date = None
    valid_formats = ["%Y-%m-%d", "%Y/%m/%d"]
    for vf in valid_formats:
        try:
            ymd_date = datetime.strptime(ymd_str, vf).date()
            break
        except:
            donothing = True
    assert ymd_date != None
    return ymd_date


# Given a dob str in the form YYYY-MM-DD, return the current age in years (including decimal places)
def AgeFromDOB(dob_str):
    assert type(dob_str) == str

    dob_date = ymd_to_date(dob_str)

    # compute years based on birthday, and extra time since then
    # NOTE: we don't really need this to be perfect, so we're not worrying about timezones and stuff

    cur_date = datetime.now().date()

    dob_year = dob_date.year
    dob_month = dob_date.month
    dob_day = dob_date.day

    cur_year = cur_date.year
    last_year = cur_year - 1
    next_year = cur_year + 1

    bday_thisyear = datetime(cur_year, dob_month, dob_day).date()
    bday_lastyear = datetime(last_year, dob_month, dob_day).date()
    bday_nextyear = datetime(next_year, dob_month, dob_day).date()

    if cur_date >= bday_thisyear:
        age_years = (cur_year - dob_year) + (
            cur_date - bday_thisyear
        ).total_seconds() / (bday_nextyear - bday_thisyear).total_seconds()
    else:
        age_years = (last_year - dob_year) + (
            cur_date - bday_lastyear
        ).total_seconds() / (bday_thisyear - bday_lastyear).total_seconds()

    return age_years


# Given a roman name, make a capitalized version
# e.g., YONG HYEIN -> Yong Hyein
def recapitalize(s):
    return " ".join([x.capitalize() for x in s.split(" ")])


# Given a dictionary of values produce a dictionary of ranks based on those values
# e.g.: {"a": 1, "b": 3.3, "c": 0.5, "d": 1} ->
#       {"a": 2, "b": 4, "c": 1, "d": 2}
def val_dict_to_rank_dict(d, reverse=False):
    table = sorted(
        [(val, key) for key, val in d.items() if (val != None) and not np.isnan(val)],
        reverse=reverse,
    )
    rank_dict = {}
    for j in range(0, len(table)):
        this_item = table[j]
        if j == 0:
            rank_dict[this_item[1]] = j + 1
        else:
            prev_item = table[j - 1]
            if prev_item[0] == this_item[0]:
                rank_dict[this_item[1]] = rank_dict[prev_item[1]]
            else:
                rank_dict[this_item[1]] = j + 1

    for key in d:
        if d[key] == None:
            rank_dict[key] = None
        elif np.isnan(d[key]):
            rank_dict[key] = np.nan

    return rank_dict


# Save df to json table for datatables consumption
def df_to_json_table(df, filepath=None):
    this_json = df.to_json(force_ascii=False, orient="split", index=False)
    # rename "columns" to "header" and arrange on separate lines
    this_json_data = json.loads(this_json)
    this_json_data["header"] = this_json_data.pop("columns")
    this_json_data["data"] = this_json_data.pop("data")
    # note: the above pop-push keeps header ahead of data,
    # since Python 3.7 guarantees insertion order
    if filepath == None:
        return json.dumps(this_json_data, indent=0, ensure_ascii=False)
    else:
        with open(filepath, "w") as f:
            json.dump(this_json_data, f, indent=0, ensure_ascii=False)


# dump json and replace each NaN with null
# This simply does a string replacement. However, there is no reason
# we should ever encounter "NaN" (with that capitalization) in general,
# so it's probably okay.
def dump_json_nan_null(data, filepath, indent=0, ensure_ascii=False):
    s = json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)
    s = re.sub(r"\bNaN\b", "null", s)
    with open(filepath, "w") as f:
        f.write(s)


# english district names
def district_to_en(district):
    district_english_table = {
        "강원 강릉시": "Gangwon | Gangneung",
        "강원 동해시태백시삼척시정선군": "Gangwon | Donghae-Taebaek-Samcheok-Jeongseon",
        "강원 속초시인제군고성군양양군": "Gangwon | Sokcho-Inje-Goseong-Yangyang",
        "강원 원주시갑": "Gangwon | Wonju A",
        "강원 원주시을": "Gangwon | Wonju B",
        "강원 춘천시철원군화천군양구군갑": "Gangwon | Chuncheon-Cheorwon-Hwacheon-Yanggu A",
        "강원 춘천시철원군화천군양구군을": "Gangwon | Chuncheon-Cheorwon-Hwacheon-Yanggu B",
        "강원 홍천군횡성군": "Gangwon | Hongcheon-Hoengseong",
        "경기 고양시갑": "Gyeonggi | Goyang A",
        "경기 고양시을": "Gyeonggi | Goyang B",
        "경기 고양시병": "Gyeonggi | Goyang C",
        "경기 고양시정": "Gyeonggi | Goyang D",
        "경기 광명시갑": "Gyeonggi | Gwangmyeong A",
        "경기 광명시을": "Gyeonggi | Gwangmyeong B",
        "경기 광주시갑": "Gyeonggi | Gwangju A",
        "경기 광주시을": "Gyeonggi | Gwangju B",
        "경기 구리시": "Gyeonggi | Guri",
        "경기 군포시": "Gyeonggi | Gunpo",
        "경기 김포시갑": "Gyeonggi | Gimpo A",
        "경기 김포시을": "Gyeonggi | Gimpo B",
        "경기 남양주시갑": "Gyeonggi | Namyangju A",
        "경기 남양주시을": "Gyeonggi | Namyangju B",
        "경기 남양주시병": "Gyeonggi | Namyangju C",
        "경기 동두천시연천군": "Gyeonggi | Dongducheon-Yeoncheon",
        "경기 부천시갑": "Gyeonggi | Bucheon A",
        "경기 부천시을": "Gyeonggi | Bucheon B",
        "경기 부천시병": "Gyeonggi | Bucheon C",
        "경기 부천시정": "Gyeonggi | Bucheon D",
        "경기 성남시분당구갑": "Gyeonggi | Seongnam Bundang A",
        "경기 성남시분당구을": "Gyeonggi | Seongnam Bundang B",
        "경기 성남시수정구": "Gyeonggi | Seongnam Sujeong",
        "경기 성남시중원구": "Gyeonggi | Seongnam Jungwon",
        "경기 수원시갑": "Gyeonggi | Suwon A",
        "경기 수원시을": "Gyeonggi | Suwon B",
        "경기 수원시병": "Gyeonggi | Suwon C",
        "경기 수원시정": "Gyeonggi | Suwon D",
        "경기 수원시무": "Gyeonggi | Suwon E",
        "경기 시흥시갑": "Gyeonggi | Siheung A",
        "경기 시흥시을": "Gyeonggi | Siheung B",
        "경기 안산시단원구갑": "Gyeonggi | Ansan Danwon A",
        "경기 안산시단원구을": "Gyeonggi | Ansan Danwon B",
        "경기 안산시상록구갑": "Gyeonggi | Ansan Sangnok A",
        "경기 안산시상록구을": "Gyeonggi | Ansan Sangnok B",
        "경기 안성시": "Gyeonggi | Anseong",
        "경기 안양시동안구갑": "Gyeonggi | Anyang Dongan A",
        "경기 안양시동안구을": "Gyeonggi | Anyang Dongan B",
        "경기 안양시만안구": "Gyeonggi | Anyang Manan",
        "경기 양주시": "Gyeonggi | Yangju",
        "경기 여주시양평군": "Gyeonggi | Yeoju-Yangpyeong",
        "경기 오산시": "Gyeonggi | Osan",
        "경기 용인시갑": "Gyeonggi | Yongin A",
        "경기 용인시을": "Gyeonggi | Yongin B",
        "경기 용인시병": "Gyeonggi | Yongin C",
        "경기 용인시정": "Gyeonggi | Yongin D",
        "경기 의왕시과천시": "Gyeonggi | Uiwang-Gwacheon",
        "경기 의정부시갑": "Gyeonggi | Uijeongbu A",
        "경기 의정부시을": "Gyeonggi | Uijeongbu B",
        "경기 이천시": "Gyeonggi | Icheon",
        "경기 파주시갑": "Gyeonggi | Paju A",
        "경기 파주시을": "Gyeonggi | Paju B",
        "경기 평택시갑": "Gyeonggi | Pyeongtaek A",
        "경기 평택시을": "Gyeonggi | Pyeongtaek B",
        "경기 포천시가평군": "Gyeonggi | Pocheon-Gapyeong",
        "경기 하남시": "Gyeonggi | Hanam",
        "경기 화성시갑": "Gyeonggi | Hwaseong A",
        "경기 화성시을": "Gyeonggi | Hwaseong B",
        "경기 화성시병": "Gyeonggi | Hwaseong C",
        "경남 거제시": "S. Gyeongsang | Geoje",
        "경남 김해시갑": "S. Gyeongsang | Gimhae A",
        "경남 김해시을": "S. Gyeongsang | Gimhae B",
        "경남 밀양시의령군함안군창녕군": "S. Gyeongsang | Miryang-Uiryeong-Haman-Changnyeong",
        "경남 사천시남해군하동군": "S. Gyeongsang | Sacheon-Namhae-Hadong",
        "경남 산청군함양군거창군합천군": "S. Gyeongsang | Sancheong-Hamyang-Geochang-Hapcheon",
        "경남 양산시갑": "S. Gyeongsang | Yangsan A",
        "경남 양산시을": "S. Gyeongsang | Yangsan B",
        "경남 진주시갑": "S. Gyeongsang | Jinju A",
        "경남 진주시을": "S. Gyeongsang | Jinju B",
        "경남 창원시마산합포구": "S. Gyeongsang | Changwon Masanhappo",
        "경남 창원시마산회원구": "S. Gyeongsang | Changwon Masanhoewon",
        "경남 창원시성산구": "S. Gyeongsang | Changwon Seongsan",
        "경남 창원시의창구": "S. Gyeongsang | Changwon Uichang",
        "경남 창원시진해구": "S. Gyeongsang | Changwon Jinhae",
        "경남 통영시고성군": "S. Gyeongsang | Tongyeong-Goseong",
        "경북 경산시": "N. Gyeongsang | Gyeongsan",
        "경북 경주시": "N. Gyeongsang | Gyeongju",
        "경북 고령군성주군칠곡군": "N. Gyeongsang | Goryeong-Seongju-Chilgok",
        "경북 구미시갑": "N. Gyeongsang | Gumi A",
        "경북 구미시을": "N. Gyeongsang | Gumi B",
        "경북 군위군의성군청송군영덕군": "N. Gyeongsang | Gunwi-Uiseong-Cheongsong-Yeongdeok",
        "경북 김천시": "N. Gyeongsang | Gimcheon",
        "경북 상주시문경시": "N. Gyeongsang | Sangju-Mungyeong",
        "경북 안동시예천군": "N. Gyeongsang | Andong-Yecheon",
        "경북 영주시영양군봉화군울진군": "N. Gyeongsang | Yeongju-Yeongyang-Bonghwa-Uljin",
        "경북 영천시청도군": "N. Gyeongsang | Yeongcheon-Cheongdo",
        "경북 포항시남구울릉군": "N. Gyeongsang | Pohang Nam-Ulleung",
        "경북 포항시북구": "N. Gyeongsang | Pohang Buk",
        "광주 광산구갑": "Gwangju | Gwangsan A",
        "광주 광산구을": "Gwangju | Gwangsan B",
        "광주 동구남구갑": "Gwangju | Dong-Nam A",
        "광주 동구남구을": "Gwangju | Dong-Nam B",
        "광주 북구갑": "Gwangju | Buk A",
        "광주 북구을": "Gwangju | Buk B",
        "광주 서구갑": "Gwangju | Seo A",
        "광주 서구을": "Gwangju | Seo B",
        "대구 달서구갑": "Daegu | Dalseo A",
        "대구 달서구을": "Daegu | Dalseo B",
        "대구 달서구병": "Daegu | Dalseo C",
        "대구 달성군": "Daegu | Dalseong",
        "대구 동구갑": "Daegu | Dong A",
        "대구 동구을": "Daegu | Dong B",
        "대구 북구갑": "Daegu | Buk A",
        "대구 북구을": "Daegu | Buk B",
        "대구 서구": "Daegu | Seo",
        "대구 수성구갑": "Daegu | Suseong A",
        "대구 수성구을": "Daegu | Suseong B",
        "대구 중구남구": "Daegu | Jung-Nam",
        "대전 대덕구": "Daejeon | Daedeok",
        "대전 동구": "Daejeon | Dong",
        "대전 서구갑": "Daejeon | Seo A",
        "대전 서구을": "Daejeon | Seo B",
        "대전 유성구갑": "Daejeon | Yuseong A",
        "대전 유성구을": "Daejeon | Yuseong B",
        "대전 중구": "Daejeon | Jung",
        "부산 금정구": "Busan | Geumjeong",
        "부산 기장군": "Busan | Gijang",
        "부산 남구갑": "Busan | Nam A",
        "부산 남구을": "Busan | Nam B",
        "부산 동래구": "Busan | Dongnae",
        "부산 진구갑": "Busan | Busanjin A",
        "부산 부산진구을": "Busan | Busanjin B",
        "부산 북구강서구갑": "Busan | Buk-Gangseo A",
        "부산 북구강서구을": "Busan | Buk-Gangseo B",
        "부산 사상구": "Busan | Sasang",
        "부산 사하구갑": "Busan | Saha A",
        "부산 사하구을": "Busan | Saha B",
        "부산 서구동구": "Busan | Seo-Dong",
        "부산 수영구": "Busan | Suyeong",
        "부산 연제구": "Busan | Yeonje",
        "부산 중구영도구": "Busan | Jung-Yeongdo",
        "부산 해운대구갑": "Busan | Haeundae A",
        "부산 해운대구을": "Busan | Haeundae B",
        "비례대표": "Proportional seat",
        "서울 강남구갑": "Seoul | Gangnam A",
        "서울 강남구을": "Seoul | Gangnam B",
        "서울 강남구병": "Seoul | Gangnam C",
        "서울 강동구갑": "Seoul | Gangdong A",
        "서울 강동구을": "Seoul | Gangdong B",
        "서울 강북구갑": "Seoul | Gangbuk A",
        "서울 강북구을": "Seoul | Gangbuk B",
        "서울 강서구갑": "Seoul | Gangseo A",
        "서울 강서구을": "Seoul | Gangseo B",
        "서울 강서구병": "Seoul | Gangseo C",
        "서울 관악구갑": "Seoul | Gwanak A",
        "서울 관악구을": "Seoul | Gwanak B",
        "서울 광진구갑": "Seoul | Gwangjin A",
        "서울 광진구을": "Seoul | Gwangjin B",
        "서울 구로구갑": "Seoul | Guro A",
        "서울 구로구을": "Seoul | Guro B",
        "서울 금천구": "Seoul | Geumcheon",
        "서울 노원구갑": "Seoul | Nowon A",
        "서울 노원구을": "Seoul | Nowon B",
        "서울 노원구병": "Seoul | Nowon C",
        "서울 도봉구갑": "Seoul | Dobong A",
        "서울 도봉구을": "Seoul | Dobong B",
        "서울 동대문구갑": "Seoul | Dongdaemun A",
        "서울 동대문구을": "Seoul | Dongdaemun B",
        "서울 동작구갑": "Seoul | Dongjak A",
        "서울 동작구을": "Seoul | Dongjak B",
        "서울 마포구갑": "Seoul | Mapo A",
        "서울 마포구을": "Seoul | Mapo B",
        "서울 서대문구갑": "Seoul | Seodaemun A",
        "서울 서대문구을": "Seoul | Seodaemun B",
        "서울 서초구갑": "Seoul | Seocho A",
        "서울 서초구을": "Seoul | Seocho B",
        "서울 성북구갑": "Seoul | Seongbuk A",
        "서울 성북구을": "Seoul | Seongbuk B",
        "서울 송파구갑": "Seoul | Songpa A",
        "서울 송파구을": "Seoul | Songpa B",
        "서울 송파구병": "Seoul | Songpa C",
        "서울 양천구갑": "Seoul | Yangcheon A",
        "서울 양천구을": "Seoul | Yangcheon B",
        "서울 영등포구갑": "Seoul | Yeongdeungpo A",
        "서울 영등포구을": "Seoul | Yeongdeungpo B",
        "서울 용산구": "Seoul | Yongsan",
        "서울 은평구갑": "Seoul | Eunpyeong A",
        "서울 은평구을": "Seoul | Eunpyeong B",
        "서울 종로구": "Seoul | Jongno",
        "서울 중구성동구갑": "Seoul | Jung-Seongdong A",
        "서울 중구성동구을": "Seoul | Jung-Seongdong B",
        "서울 중랑구갑": "Seoul | Jungnang A",
        "서울 중랑구을": "Seoul | Jungnang B",
        "세종특별자치시갑": "Sejong | Sejong A",
        "세종특별자치시을": "Sejong | Sejong B",
        "울산 남구갑": "Ulsan | Nam A",
        "울산 남구을": "Ulsan | Nam B",
        "울산 동구": "Ulsan | Dong",
        "울산 북구": "Ulsan | Buk",
        "울산 울주군": "Ulsan | Ulju",
        "울산 중구": "Ulsan | Jung",
        "인천 계양구갑": "Incheon | Gyeyang A",
        "인천 계양구을": "Incheon | Gyeyang B",
        "인천 남동구갑": "Incheon | Namdong A",
        "인천 남동구을": "Incheon | Namdong B",
        "인천 동구미추홀구갑": "Incheon | Dong-Michuhol A",
        "인천 동구미추홀구을": "Incheon | Dong-Michuhol B",
        "인천 부평구갑": "Incheon | Bupyeong A",
        "인천 부평구을": "Incheon | Bupyeong B",
        "인천 서구갑": "Incheon | Seo A",
        "인천 서구을": "Incheon | Seo B",
        "인천 연수구갑": "Incheon | Yeonsu A",
        "인천 연수구을": "Incheon | Yeonsu B",
        "인천 중구강화군옹진군": "Incheon | Jung-Ganghwa-Ongjin",
        "전남 고흥군보성군장흥군강진군": "S. Jeolla | Goheung-Boseong-Jangheung-Gangjin",
        "전남 나주시화순군": "S. Jeolla | Naju-Hwasun",
        "전남 담양군함평군영광군장성군": "S. Jeolla | Damyang-Hampyeong-Yeonggwang-Jangseong",
        "전남 목포시": "S. Jeolla | Mokpo",
        "전남 순천시광양시곡성군구례군갑": "S. Jeolla | Suncheon-Gwangyang-Gokseong-Gurye A",
        "전남 순천시광양시곡성군구례군을": "S. Jeolla | Suncheon-Gwangyang-Gokseong-Gurye B",
        "전남 여수시갑": "S. Jeolla | Yeosu A",
        "전남 여수시을": "S. Jeolla | Yeosu B",
        "전남 영암군무안군신안군": "S. Jeolla | Yeongam-Muan-Sinan",
        "전남 해남군완도군진도군": "S. Jeolla | Haenam-Wando-Jindo",
        "전북 군산시": "N. Jeolla | Gunsan",
        "전북 김제시부안군": "N. Jeolla | Gimje-Buan",
        "전북 남원시임실군순창군": "N. Jeolla | Namwon-Imsil-Sunchang",
        "전북 완주군진안군무주군장수군": "N. Jeolla | Wanju-Jinan-Muju-Jangsu",
        "전북 익산시갑": "N. Jeolla | Iksan A",
        "전북 익산시을": "N. Jeolla | Iksan B",
        "전북 전주시갑": "N. Jeolla | Jeonju A",
        "전북 전주시을": "N. Jeolla | Jeonju B",
        "전북 전주시병": "N. Jeolla | Jeonju C",
        "전북 정읍시고창군": "N. Jeolla | Jeongeup-Gochang",
        "제주 서귀포시": "Jeju | Seogwipo",
        "제주 제주시갑": "Jeju | Jeju A",
        "제주 제주시을": "Jeju | Jeju B",
        "충남 공주시부여군청양군": "S. Chungcheong | Gongju-Buyeo-Cheongyang",
        "충남 논산시계룡시금산군": "S. Chungcheong | Nonsan-Gyeryong-Geumsan",
        "충남 당진시": "S. Chungcheong | Dangjin",
        "충남 보령시서천군": "S. Chungcheong | Boryeong-Seocheon",
        "충남 서산시태안군": "S. Chungcheong | Seosan-Taean",
        "충남 아산시갑": "S. Chungcheong | Asan A",
        "충남 아산시을": "S. Chungcheong | Asan B",
        "충남 천안시갑": "S. Chungcheong | Cheonan A",
        "충남 천안시을": "S. Chungcheong | Cheonan B",
        "충남 천안시병": "S. Chungcheong | Cheonan C",
        "충남 홍성군예산군": "S. Chungcheong | Hongseong-Yesan",
        "충북 보은군옥천군영동군괴산군": "N. Chungcheong | Boeun-Okcheon-Yeongdong-Goesan",
        "충북 제천시단양군": "N. Chungcheong | Jecheon-Danyang",
        "충북 증평군진천군괴산군음성군": "N. Chungcheong | Jeungpyeong-Jincheon-Eumseong",
        "충북 청주시상당구": "N. Chungcheong | Cheongju Sangdang",
        "충북 청주시서원구": "N. Chungcheong | Cheongju Seowon",
        "충북 청주시청원구": "N. Chungcheong | Cheongju Cheongwon",
        "충북 청주시흥덕구": "N. Chungcheong | Cheongju Heungdeok",
        "충북 충주시": "N. Chungcheong | Cheongju",
    }
    return district_english_table.get(district, district)
