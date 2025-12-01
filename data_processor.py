"""
데이터 전처리 및 유망주 점수 계산 모듈
새 데이터셋 (dataset_new.csv) 및 기존 데이터셋 (dataset.csv) 지원
"""
import pandas as pd
import numpy as np


class FootballDataProcessor:
    """축구 선수 데이터를 처리하고 유망주 점수를 계산하는 클래스"""
    
    # 새 데이터셋 컬럼 매핑 (약어 -> 전체 이름)
    COLUMN_MAPPING = {
        'Acc': 'Acceleration',
        'Wor': 'Workrate',
        'Vis': 'Vision',
        'Thr': 'Throwing',
        'Tec': 'Technique',
        'Tea': 'Teamwork',
        'Tck': 'Tackling',
        'Str': 'Strength',
        'Sta': 'Stamina',
        'TRO': 'RushingOut',
        'Ref': 'Reflexes',
        'Pun': 'TendencyToPunch',
        'Pos': 'Positioning',
        'Pen': 'PenaltyTaking',
        'Pas': 'Passing',
        'Pac': 'Pace',
        '1v1': 'OneOnOnes',
        'OtB': 'OffTheBall',
        'Nat.1': 'NaturalFitness',
        'Mar': 'Marking',
        'L Th': 'Longthrows',
        'Lon': 'LongShots',
        'Ldr': 'Leadership',
        'Kic': 'Kicking',
        'Jum': 'Jumping',
        'Hea': 'Heading',
        'Han': 'Handling',
        'Fre': 'Freekicks',
        'Fla': 'Flair',
        'Fir': 'FirstTouch',
        'Fin': 'Finishing',
        'Ecc': 'Eccentricity',
        'Dri': 'Dribbling',
        'Det': 'Determination',
        'Dec': 'Decisions',
        'Cro': 'Crossing',
        'Cor': 'Corners',
        'Cnt': 'Concentration',
        'Cmp': 'Composure',
        'Com': 'Communication',
        'Cmd': 'CommandOfArea',
        'Bra': 'Bravery',
        'Bal': 'Balance',
        'Ant': 'Anticipation',
        'Agi': 'Agility',
        'Agg': 'Aggression',
        'Aer': 'AerialAbility',
        'Vers': 'Versatility',
        'Temp': 'Temperament',
        'Spor': 'Sportsmanship',
        'Prof': 'Professional',
        'Pres': 'Pressure',
        'Loy': 'Loyalty',
        'Inj Pr': 'InjuryProness',
        'Imp M': 'ImportantMatches',
        'Dirt': 'Dirtiness',
        'Amb': 'Ambition',
        'Ada': 'Adaptability',
        'Cons': 'Consistency',
        'Cont': 'Controversy',
        'Nat': 'NationID',
        'Left Foot': 'LeftFoot',
        'Right Foot': 'RightFoot'
    }
    
    # 능력치 카테고리별 컬럼 정의
    TECHNICAL_ATTRIBUTES = [
        'Corners', 'Crossing', 'Dribbling', 'Finishing', 'FirstTouch',
        'Freekicks', 'Heading', 'LongShots', 'Marking', 'Passing',
        'PenaltyTaking', 'Tackling', 'Technique', 'Handling', 'Kicking', 'OneOnOnes', 'Reflexes', 'RushingOut', 'Throwing'
    ]
    
    MENTAL_ATTRIBUTES = [
        'Aggression', 'Anticipation', 'Bravery', 'Composure', 'Concentration',
        'Vision', 'Decisions', 'Determination', 'Flair', 'Leadership',
        'OffTheBall', 'Positioning', 'Teamwork', 'Workrate', 'CommandOfArea', 'Communication', 'Eccentricity'
    ]
    
    PHYSICAL_ATTRIBUTES = [
        'Acceleration', 'Agility', 'Balance', 'Jumping', 'NaturalFitness',
        'Pace', 'Stamina', 'Strength', 'AerialAbility'
    ]
    
    # 포지션별 중요 능력치
    POSITION_ATTRIBUTES = {
        'Goalkeeper': ['AerialAbility', 'CommandOfArea', 'Handling', 'Kicking', 
                      'OneOnOnes', 'Reflexes', 'RushingOut', 'Throwing'],
        'Defender': ['Marking', 'Tackling', 'Heading', 'Positioning', 'Strength',
                    'Anticipation', 'Bravery', 'Concentration'],
        'Midfielder': ['Passing', 'Vision', 'Technique', 'FirstTouch', 'Stamina',
                      'Workrate', 'Decisions', 'Teamwork'],
        'Forward': ['Finishing', 'Dribbling', 'Pace', 'Acceleration', 'OffTheBall',
                   'Composure', 'FirstTouch', 'Technique']
    }
    
    def __init__(self, csv_path):
        """
        데이터 프로세서 초기화
        
        Args:
            csv_path: CSV 파일 경로
        """
        self.csv_path = csv_path
        self.df = None
        self.processed_df = None
        self.is_new_format = False  # 새 데이터셋 형식 여부
        
    def load_data(self):
        """CSV 데이터 로드"""
        print("데이터를 로딩 중...")
        self.df = pd.read_csv(self.csv_path)
        print(f"총 {len(self.df)} 명의 선수 데이터를 로드했습니다.")
        
        # 새 데이터셋 형식인지 확인 (약어 컬럼이 있는지)
        if 'Acc' in self.df.columns or 'Fin' in self.df.columns:
            self.is_new_format = True
            print("새 데이터셋 형식이 감지되었습니다. 컬럼명을 변환합니다...")
            self._convert_column_names()
        
        return self.df
    
    def _convert_column_names(self):
        """새 데이터셋의 약어 컬럼명을 전체 이름으로 변환"""
        # 컬럼명 변환
        self.df = self.df.rename(columns=self.COLUMN_MAPPING)
        
        # Height 변환 (예: "5'9"" -> 175 cm)
        if 'Height' in self.df.columns:
            self.df['Height'] = self.df['Height'].apply(self._convert_height)
        
        # Weight 변환 (예: "65 kg" -> 65)
        if 'Weight' in self.df.columns:
            self.df['Weight'] = self.df['Weight'].apply(self._convert_weight)
        
        # 새 데이터셋의 Position 컬럼 처리
        if 'Position' in self.df.columns and 'PositionsDesc' not in self.df.columns:
            self.df['PositionsDesc'] = self.df['Position']
            self._create_position_columns()
        
        print(f"컬럼 변환 완료: {len(self.df.columns)}개 컬럼")
    
    def _convert_height(self, height_str):
        """Height 문자열을 cm로 변환 (예: 5'9" -> 175)"""
        if pd.isna(height_str):
            return None
        try:
            height_str = str(height_str).strip()
            if "'" in height_str:
                # 피트/인치 형식 (예: 5'9")
                parts = height_str.replace('"', '').split("'")
                feet = int(parts[0])
                inches = int(parts[1]) if len(parts) > 1 and parts[1] else 0
                return int(feet * 30.48 + inches * 2.54)
            elif 'cm' in height_str.lower():
                return int(float(height_str.lower().replace('cm', '').strip()))
            else:
                return int(float(height_str))
        except:
            return None
    
    def _convert_weight(self, weight_str):
        """Weight 문자열을 kg로 변환 (예: 65 kg -> 65)"""
        if pd.isna(weight_str):
            return None
        try:
            weight_str = str(weight_str).strip().lower()
            if 'kg' in weight_str:
                return int(float(weight_str.replace('kg', '').strip()))
            elif 'lb' in weight_str or 'lbs' in weight_str:
                lbs = float(weight_str.replace('lbs', '').replace('lb', '').strip())
                return int(lbs * 0.453592)
            else:
                return int(float(weight_str))
        except:
            return None
    
    def _create_position_columns(self):
        """새 데이터셋의 Position 문자열에서 포지션 컬럼 생성"""
        # 포지션 매핑 (새 형식 -> 기존 형식)
        position_mapping = {
            'GK': 'Goalkeeper',
            'D (C)': 'DefenderCentral',
            'D (L)': 'DefenderLeft',
            'D (R)': 'DefenderRight',
            'D (LC)': 'DefenderCentral',
            'D (RC)': 'DefenderCentral',
            'D (RL)': 'DefenderCentral',
            'D/WB (L)': 'WingBackLeft',
            'D/WB (R)': 'WingBackRight',
            'WB (L)': 'WingBackLeft',
            'WB (R)': 'WingBackRight',
            'DM': 'DefensiveMidfielder',
            'DM (C)': 'DefensiveMidfielder',
            'M (C)': 'MidfielderCentral',
            'M (L)': 'MidfielderLeft',
            'M (R)': 'MidfielderRight',
            'M (LC)': 'MidfielderCentral',
            'M (RC)': 'MidfielderCentral',
            'M/AM (C)': 'MidfielderCentral',
            'AM (C)': 'AttackingMidCentral',
            'AM (L)': 'AttackingMidLeft',
            'AM (R)': 'AttackingMidRight',
            'AM (LC)': 'AttackingMidCentral',
            'AM (RC)': 'AttackingMidCentral',
            'AM (RL)': 'AttackingMidCentral',
            'AM (RLC)': 'AttackingMidCentral',
            'M (RLC)': 'MidfielderCentral',
            'D (RLC)': 'DefenderCentral',
            'WB (RL)': 'WingBackRight',
            'ST': 'Striker',
            'ST (C)': 'Striker',
        }
        
        # 모든 포지션 컬럼 초기화
        position_cols = [
            'Goalkeeper', 'Sweeper', 'Striker', 'AttackingMidCentral',
            'AttackingMidLeft', 'AttackingMidRight', 'DefenderCentral',
            'DefenderLeft', 'DefenderRight', 'DefensiveMidfielder',
            'MidfielderCentral', 'MidfielderLeft', 'MidfielderRight',
            'WingBackLeft', 'WingBackRight'
        ]
        
        for col in position_cols:
            self.df[col] = 0
        
        # Position 문자열 파싱하여 해당 포지션에 20 부여
        def parse_position(pos_str):
            if pd.isna(pos_str):
                return {}
            
            result = {}
            # 쉼표나 공백으로 분리된 포지션들 처리
            positions = str(pos_str).replace(',', '/').split('/')
            
            for pos in positions:
                pos = pos.strip()
                if pos in position_mapping:
                    mapped = position_mapping[pos]
                    result[mapped] = 20
                else:
                    # 부분 매칭 시도
                    for key, value in position_mapping.items():
                        if key in pos or pos in key:
                            result[value] = 20
                            break
            
            return result
        
        # 각 행에 대해 포지션 파싱
        for idx, row in self.df.iterrows():
            pos_dict = parse_position(row.get('Position', ''))
            for pos_col, value in pos_dict.items():
                if pos_col in self.df.columns:
                    self.df.at[idx, pos_col] = value
    
    def calculate_overall_rating(self):
        """종합 능력치 계산 (기술/정신/신체 능력치 평균)"""
        # 존재하는 컬럼만 사용
        tech_attrs = [a for a in self.TECHNICAL_ATTRIBUTES if a in self.df.columns]
        mental_attrs = [a for a in self.MENTAL_ATTRIBUTES if a in self.df.columns]
        phys_attrs = [a for a in self.PHYSICAL_ATTRIBUTES if a in self.df.columns]
        
        self.df['Technical_Rating'] = self.df[tech_attrs].mean(axis=1) if tech_attrs else 0
        self.df['Mental_Rating'] = self.df[mental_attrs].mean(axis=1) if mental_attrs else 0
        self.df['Physical_Rating'] = self.df[phys_attrs].mean(axis=1) if phys_attrs else 0
        
        # 종합 평점 (세 카테고리의 평균)
        self.df['Overall_Rating'] = (
            self.df['Technical_Rating'] * 0.4 +
            self.df['Mental_Rating'] * 0.35 +
            self.df['Physical_Rating'] * 0.25
        )
        
        return self.df
    
    def calculate_potential_score(self):
        """
        잠재력 점수 계산
        나이가 어릴수록, 현재 능력치가 높을수록 높은 점수
        """
        # 나이 가중치: 젊을수록 높은 가중치
        # 18-21세: 1.5배, 22-25세: 1.2배, 26-29세: 1.0배, 30세 이상: 0.5배
        age_weight = np.where(self.df['Age'] <= 21, 1.0,
                     np.where(self.df['Age'] <= 25, 1.0,
                     np.where(self.df['Age'] <= 29, 1.0, 1.0)))
        
        self.df['Age_Weight'] = age_weight
        self.df['Potential_Score'] = self.df['Overall_Rating'] * age_weight
        
        return self.df
    
    def identify_primary_position(self):
        """선수의 주 포지션 식별"""
        position_cols = [
            'Goalkeeper', 'Sweeper', 'Striker', 'AttackingMidCentral',
            'AttackingMidLeft', 'AttackingMidRight', 'DefenderCentral',
            'DefenderLeft', 'DefenderRight', 'DefensiveMidfielder',
            'MidfielderCentral', 'MidfielderLeft', 'MidfielderRight',
            'WingBackLeft', 'WingBackRight'
        ]
        
        # 존재하는 포지션 컬럼만 사용
        available_pos_cols = [col for col in position_cols if col in self.df.columns]
        
        if available_pos_cols:
            # 각 선수의 최고 포지션 숙련도 찾기
            position_values = self.df[available_pos_cols]
            self.df['Primary_Position'] = position_values.idxmax(axis=1)
            self.df['Position_Rating'] = position_values.max(axis=1)
        else:
            # 새 데이터셋에서 Position 문자열로 직접 파싱
            self.df['Primary_Position'] = self.df.get('PositionsDesc', 'Unknown')
            self.df['Position_Rating'] = 15
        
        # 포지션 카테고리 매핑
        def categorize_position(pos):
            pos_str = str(pos).upper() if pd.notna(pos) else ''
            
            if 'GK' in pos_str or 'GOALKEEPER' in pos_str:
                return 'Goalkeeper'
            elif any(x in pos_str for x in ['DEFENDER', 'D (', 'D/', 'SWEEPER', 'WINGBACK', 'WB']):
                return 'Defender'
            elif any(x in pos_str for x in ['MIDFIELDER', 'M (', 'AM (', 'DM', 'ATTACKING']):
                return 'Midfielder'
            elif any(x in pos_str for x in ['STRIKER', 'ST', 'FORWARD']):
                return 'Forward'
            else:
                # Primary_Position 컬럼 값으로 분류
                if 'Goalkeeper' in pos:
                    return 'Goalkeeper'
                elif 'Defender' in pos or 'Sweeper' in pos or 'WingBack' in pos:
                    return 'Defender'
                elif 'Midfielder' in pos or 'Attacking' in pos or 'Defensive' in pos:
                    return 'Midfielder'
                elif 'Striker' in pos:
                    return 'Forward'
                else:
                    return 'Midfielder'
        
        self.df['Position_Category'] = self.df['Primary_Position'].apply(categorize_position)
        
        return self.df
    
    def calculate_position_specialized_score(self):
        """포지션별 특화 점수 계산"""
        def get_position_score(row):
            category = row['Position_Category']
            if category in self.POSITION_ATTRIBUTES:
                attrs = self.POSITION_ATTRIBUTES[category]
                available_attrs = [attr for attr in attrs if attr in self.df.columns]
                if available_attrs:
                    return row[available_attrs].mean()
            return row['Overall_Rating']
        
        self.df['Position_Specialized_Score'] = self.df.apply(get_position_score, axis=1)
        
        return self.df
    
    def calculate_talent_score(self):
        """
        최종 유망주 점수 계산
        = 종합 능력치 (40%) + 잠재력 점수 (40%) + 포지션 특화 점수 (20%)
        """
        self.df['Talent_Score'] = (
            self.df['Overall_Rating'] * 0.4 +
            self.df['Potential_Score'] * 0.4 +
            self.df['Position_Specialized_Score'] * 0.2
        )
        
        # 정규화 (0-100 범위)
        min_score = self.df['Talent_Score'].min()
        max_score = self.df['Talent_Score'].max()
        if max_score > min_score:
            self.df['Talent_Score_Normalized'] = ((self.df['Talent_Score'] - min_score) / 
                                                   (max_score - min_score) * 100)
        else:
            self.df['Talent_Score_Normalized'] = 50
        
        return self.df
    
    def process_all(self):
        """전체 데이터 처리 파이프라인 실행"""
        print("데이터 처리를 시작합니다...")
        
        # 데이터 로드
        self.load_data()
        
        # 각 단계별 처리
        print("종합 능력치를 계산 중...")
        self.calculate_overall_rating()
        
        print("잠재력 점수를 계산 중...")
        self.calculate_potential_score()
        
        print("주 포지션을 식별 중...")
        self.identify_primary_position()
        
        print("포지션별 특화 점수를 계산 중...")
        self.calculate_position_specialized_score()
        
        print("최종 유망주 점수를 계산 중...")
        self.calculate_talent_score()
        
        self.processed_df = self.df.copy()
        print("데이터 처리가 완료되었습니다!")
        
        return self.processed_df
    
    def get_top_talents(self, n=50, age_range=None, position=None, min_rating=None):
        """
        상위 유망주 선수 추출
        
        Args:
            n: 반환할 선수 수
            age_range: (min_age, max_age) 튜플
            position: 포지션 카테고리 필터
            min_rating: 최소 능력치
            
        Returns:
            필터링된 상위 유망주 DataFrame
        """
        df_filtered = self.processed_df.copy()
        
        # 필터 적용
        if age_range:
            df_filtered = df_filtered[
                (df_filtered['Age'] >= age_range[0]) & 
                (df_filtered['Age'] <= age_range[1])
            ]
        
        if position and position != 'All':
            df_filtered = df_filtered[df_filtered['Position_Category'] == position]
        
        if min_rating:
            df_filtered = df_filtered[df_filtered['Overall_Rating'] >= min_rating]
        
        # 유망주 점수로 정렬하여 상위 n명 반환
        return df_filtered.nlargest(n, 'Talent_Score_Normalized')
    
    def get_player_details(self, player_uid):
        """특정 선수의 상세 정보 반환"""
        return self.processed_df[self.processed_df['UID'] == player_uid].iloc[0]


def load_and_process_data(csv_path):
    """
    데이터 로드 및 처리 헬퍼 함수
    
    Args:
        csv_path: CSV 파일 경로
        
    Returns:
        처리된 DataFrame
    """
    processor = FootballDataProcessor(csv_path)
    return processor.process_all()
