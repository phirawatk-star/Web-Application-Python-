import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title='Platform Load Distribution', page_icon='🏗️', layout='wide')
st.title('🏗️ Platform Load Distribution — Prototype')
st.caption('แบบกรอกข้อมูล | การแบ่งแรงแบบ Bilinear ลงจุดรองรับ 4 มุม (สำหรับตรวจสอบเบื้องต้นเท่านั้น)')
st.warning('⚠️ แบบจำลองนี้ไม่ใช่การวิเคราะห์ Plate/Shell หรือ Stiffness Method และยังไม่คำนวณแรงในคาน การโก่งตัว การโก่งเดาะของ King Post หรือกำลังรับน้ำหนักฐานราก ห้ามใช้ผลลัพธ์เพื่ออนุมัติแบบหรือก่อสร้างโดยไม่ตรวจสอบด้วยแบบจำลองโครงสร้างและวิศวกรผู้รับผิดชอบ')
with st.sidebar:
    st.header('1. ขนาด Platform')
    L = st.number_input('ความยาวตามแกน X (m)', min_value=0.1, value=8.0, step=0.5)
    B = st.number_input('ความกว้างตามแกน Y (m)', min_value=0.1, value=4.0, step=0.5)
    st.header('2. แรงกระจาย')
    q = st.number_input('UDL บนพื้นที่ทั้งแผ่น (tonf/m²)', min_value=0.0, value=0.0, step=0.1)
    st.header('3. แรงล้อรถ')
    truck_weight = st.number_input('น้ำหนักรถรวม (tonf) — ข้อมูลอ้างอิง', min_value=0.0, value=25.0, step=1.0)
    st.caption('แรงล้อในตารางเป็นค่าที่ใช้คำนวณจริง น้ำหนักรถรวมด้านบนใช้ตรวจสอบยอดรวมเท่านั้น')

st.subheader('ตำแหน่ง King Post')
st.write('ต้นแบบนี้รองรับ **4 จุดรองรับที่มุม**: KP1 (0,0), KP2 (L,0), KP3 (L,B), KP4 (0,B) และสมมติว่าปฏิกิริยาเป็นแนวดิ่ง')
st.subheader('4. กรอกตำแหน่งล้อ / แรงจุด')
st.write('พิกัดวัดจากมุมซ้ายล่างของ Platform; ใช้ค่าแรงลงเป็นบวก (tonf)')
default = pd.DataFrame({'ชื่อแรง':['W1','W2','W3','W4'], 'X (m)':[2.0,2.0,5.5,5.5], 'Y (m)':[1.0,3.0,1.0,3.0], 'P (tonf)':[2.5,2.5,2.5,2.5]})
loads = st.data_editor(default, num_rows='dynamic', use_container_width=True, hide_index=True)

if st.button('🔎 วิเคราะห์การถ่ายแรง', type='primary'):
    try:
        df = loads.copy()
        for col in ['X (m)','Y (m)','P (tonf)']:
            df[col] = pd.to_numeric(df[col], errors='raise')
        if df[['X (m)','Y (m)','P (tonf)']].isna().any().any():
            st.error('มีช่องตัวเลขว่าง กรุณากรอกให้ครบ')
            st.stop()
        if ((df['X (m)']<0)|(df['X (m)']>L)|(df['Y (m)']<0)|(df['Y (m)']>B)|(df['P (tonf)']<0)).any():
            st.error('ตำแหน่งล้อต้องอยู่ใน Platform และแรงต้องไม่ติดลบ')
            st.stop()
        # Bilinear weights for four corner reactions. This is an assumed distribution rule,
        # not a stiffness-based or physically unique reaction solution for 4 supports.
        x = df['X (m)'].to_numpy()/L
        y = df['Y (m)'].to_numpy()/B
        p = df['P (tonf)'].to_numpy()
        weights = np.column_stack([(1-x)*(1-y), x*(1-y), x*y, (1-x)*y])
        r_point = (weights*p[:,None]).sum(axis=0)
        r_udl = np.full(4, q*L*B/4)
        r = r_point+r_udl
        names = ['KP1 (0,0)','KP2 (L,0)','KP3 (L,B)','KP4 (0,B)']
        result = pd.DataFrame({'King Post':names,'จากแรงล้อ (tonf)':r_point,'จาก UDL (tonf)':r_udl,'รวม (tonf)':r})
        total = p.sum()+q*L*B
        st.subheader('ผลลัพธ์')
        c1,c2,c3 = st.columns(3)
        c1.metric('แรงรวมบน Platform',f'{total:.3f} tonf')
        c2.metric('Reaction สูงสุด',f'{r.max():.3f} tonf')
        c3.metric('ผลต่างสมดุลแนวดิ่ง',f'{abs(total-r.sum()):.8f} tonf')
        st.dataframe(result.style.format(precision=3),use_container_width=True,hide_index=True)
        if len(df)>0 and abs(p.sum()-truck_weight)>1e-6:
            st.info(f'ผลรวมแรงล้อที่กรอก = {p.sum():.3f} tonf ไม่เท่ากับน้ำหนักรถอ้างอิง = {truck_weight:.3f} tonf โปรดตรวจสอบว่ากรอกครบทุกล้อหรือไม่')
        fig,ax=plt.subplots(figsize=(9,5))
        ax.plot([0,L,L,0,0],[0,0,B,B,0],'-k',linewidth=2)
        posts = [(0,0),(L,0),(L,B),(0,B)]
        for i,(px,py) in enumerate(posts):
            ax.scatter(px,py,s=110,marker='s',color='tab:blue',zorder=4)
            ax.annotate(f'KP{i+1}: {r[i]:.2f} tonf',(px,py),xytext=(5,8),textcoords='offset points',fontsize=9)
        if len(df):
            ax.scatter(df['X (m)'],df['Y (m)'],s=75,color='tab:red',zorder=5)
            for _,row in df.iterrows():
                ax.annotate(f"{row['ชื่อแรง']}: {row['P (tonf)']:.2f}",(row['X (m)'],row['Y (m)']),xytext=(5,-15),textcoords='offset points',fontsize=8)
        ax.set(xlim=(-0.1*L,1.23*L),ylim=(-0.15*B,1.20*B),xlabel='X (m)',ylabel='Y (m)',title='Platform plan: wheel loads and support reactions')
        ax.set_aspect('equal',adjustable='box');ax.grid(alpha=.2)
        st.pyplot(fig)
        st.download_button('📥 ดาวน์โหลดตาราง Reaction (CSV)',result.to_csv(index=False).encode('utf-8-sig'),file_name='king_post_reactions.csv',mime='text/csv')
        st.caption('สมมติฐาน: จุดรองรับ 4 มุม, แรงดิ่งเท่านั้น, แรงล้อแบ่งลง 4 มุมด้วย Bilinear Weights; UDL แบ่งมุมละ 1/4. วิธีนี้รักษาสมดุลแรงและโมเมนต์รวม แต่ไม่สะท้อนความแข็งคาน/พื้น/เสา หรือแรงยกที่อาจเกิดขึ้น')
    except Exception as e:
        st.error(f'ข้อมูลไม่ถูกต้อง: {e}')
